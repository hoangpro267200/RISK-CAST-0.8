"""
Public Blockchain Anchoring

Features:
1. Anchor to Ethereum/Bitcoin
2. Verify anchored data
3. Batch anchoring
"""

import os
from datetime import datetime
from typing import Optional, List, Dict
import hashlib
import json

from app.core.logging import get_logger


logger = get_logger(__name__)

# Optional web3 import
try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None
    Account = None


class EthereumAnchor:
    """
    Anchors audit data to Ethereum blockchain.
    """
    
    # Simple anchor contract ABI
    ANCHOR_ABI = [
        {
            "inputs": [
                {"name": "dataHash", "type": "bytes32"},
                {"name": "blockNumbers", "type": "uint256[]"}
            ],
            "name": "anchor",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"name": "dataHash", "type": "bytes32"}],
            "name": "getAnchor",
            "outputs": [
                {"name": "timestamp", "type": "uint256"},
                {"name": "blockNumbers", "type": "uint256[]"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "dataHash", "type": "bytes32"},
                {"indexed": False, "name": "timestamp", "type": "uint256"},
                {"indexed": False, "name": "blockNumbers", "type": "uint256[]"}
            ],
            "name": "DataAnchored",
            "type": "event"
        }
    ]
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        contract_address: Optional[str] = None,
        private_key: Optional[str] = None
    ):
        self.rpc_url = rpc_url or os.getenv("ETHEREUM_RPC_URL")
        self.contract_address = contract_address or os.getenv("ANCHOR_CONTRACT_ADDRESS")
        self.private_key = private_key or os.getenv("ANCHOR_PRIVATE_KEY")
        
        self.w3 = None
        self.contract = None
        self.account = None
        
        if WEB3_AVAILABLE and self.rpc_url:
            try:
                self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
                if self.contract_address:
                    self.contract = self.w3.eth.contract(
                        address=self.contract_address,
                        abi=self.ANCHOR_ABI
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize Ethereum connection: {e}")
        
        if WEB3_AVAILABLE and self.private_key:
            try:
                self.account = Account.from_key(self.private_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Ethereum account: {e}")
    
    async def anchor_blocks(
        self,
        block_hashes: List[str],
        block_numbers: List[int]
    ) -> Optional[str]:
        """
        Anchor multiple audit blocks to Ethereum.
        
        Args:
            block_hashes: List of block hashes to anchor
            block_numbers: Corresponding block numbers
            
        Returns:
            Transaction hash if successful
        """
        if not WEB3_AVAILABLE:
            logger.warning("web3 not installed. Install with: pip install web3")
            return None
        
        if not self.w3 or not self.contract or not self.account:
            logger.warning("Ethereum anchoring not configured")
            return None
        
        # Create combined hash of all blocks
        combined = json.dumps({
            "blocks": [
                {"hash": h, "number": n}
                for h, n in zip(block_hashes, block_numbers)
            ],
            "timestamp": datetime.utcnow().isoformat()
        }, sort_keys=True)
        
        data_hash = Web3.keccak(text=combined)
        
        try:
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.contract.functions.anchor(
                data_hash,
                block_numbers
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send
            signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                logger.info(
                    f"Blocks anchored to Ethereum",
                    extra={
                        "tx_hash": tx_hash.hex(),
                        "block_numbers": block_numbers
                    }
                )
                return tx_hash.hex()
            else:
                logger.error("Anchor transaction failed")
                return None
                
        except Exception as e:
            logger.error(f"Anchoring failed: {e}")
            return None
    
    async def verify_anchor(self, data_hash: str) -> Optional[Dict]:
        """
        Verify an anchor exists on-chain.
        
        Args:
            data_hash: Hash to verify
            
        Returns:
            Anchor data if found
        """
        if not WEB3_AVAILABLE or not self.w3 or not self.contract:
            return None
        
        try:
            result = self.contract.functions.getAnchor(
                bytes.fromhex(data_hash)
            ).call()
            
            timestamp, block_numbers = result
            
            if timestamp > 0:
                return {
                    "timestamp": datetime.fromtimestamp(timestamp),
                    "block_numbers": block_numbers,
                    "verified": True
                }
        
        except Exception as e:
            logger.error(f"Verification failed: {e}")
        
        return None


class BitcoinAnchor:
    """
    Anchors audit data to Bitcoin via OP_RETURN.
    """
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        rpc_user: Optional[str] = None,
        rpc_password: Optional[str] = None
    ):
        self.rpc_url = rpc_url or os.getenv("BITCOIN_RPC_URL")
        self.rpc_user = rpc_user or os.getenv("BITCOIN_RPC_USER")
        self.rpc_password = rpc_password or os.getenv("BITCOIN_RPC_PASSWORD")
    
    async def anchor(self, data_hash: str) -> Optional[str]:
        """
        Anchor hash to Bitcoin using OP_RETURN.
        
        Note: This is a simplified implementation.
        Production would use a proper Bitcoin library.
        """
        # Implementation would use bitcoinlib or similar
        logger.info(f"Bitcoin anchoring not yet implemented. Hash: {data_hash[:16]}...")
        return None


class AnchoringService:
    """
    Service for periodic anchoring of audit blocks.
    """
    
    def __init__(
        self,
        session,
        ethereum_anchor: Optional[EthereumAnchor] = None,
        bitcoin_anchor: Optional[BitcoinAnchor] = None
    ):
        self.session = session
        self.ethereum_anchor = ethereum_anchor or EthereumAnchor()
        self.bitcoin_anchor = bitcoin_anchor
    
    async def anchor_pending_blocks(self, batch_size: int = 10) -> List[str]:
        """
        Anchor pending (un-anchored) blocks.
        
        Returns:
            List of transaction hashes
        """
        from sqlalchemy import select
        from app.blockchain.audit_chain import AuditBlockModel
        
        # Get un-anchored blocks
        result = self.session.execute(
            select(AuditBlockModel)
            .where(AuditBlockModel.anchored == 0)
            .order_by(AuditBlockModel.block_number)
            .limit(batch_size)
        )
        blocks = result.scalars().all()
        
        if not blocks:
            return []
        
        block_hashes = [b.block_hash for b in blocks]
        block_numbers = [b.block_number for b in blocks]
        
        # Anchor to Ethereum
        tx_hash = await self.ethereum_anchor.anchor_blocks(block_hashes, block_numbers)
        
        if tx_hash:
            # Update blocks as anchored
            for block in blocks:
                block.anchored = 1
                block.anchor_tx_hash = tx_hash
            
            self.session.commit()
            
            return [tx_hash]
        
        return []
    
    async def run_periodic_anchoring(self, interval_seconds: int = 3600):
        """
        Run periodic anchoring job.
        """
        import asyncio
        
        while True:
            try:
                tx_hashes = await self.anchor_pending_blocks()
                if tx_hashes:
                    logger.info(f"Anchored blocks: {tx_hashes}")
            except Exception as e:
                logger.error(f"Periodic anchoring failed: {e}")
            
            await asyncio.sleep(interval_seconds)
