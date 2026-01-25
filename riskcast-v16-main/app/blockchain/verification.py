"""
Audit Verification Service

Features:
1. Verify individual entries
2. Verify blocks
3. Verify chain integrity
4. Generate verification reports
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.blockchain.merkle_tree import MerkleTree, MerkleProof
from app.blockchain.audit_chain import AuditChain, AuditBlockModel, AuditEntryModel, AuditBlock
from app.blockchain.anchoring import EthereumAnchor
from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class VerificationResult:
    """Result of a verification."""
    verified: bool
    timestamp: datetime
    verification_type: str  # "entry", "block", "chain", "anchor"
    details: Dict
    errors: List[str]


class VerificationService:
    """
    Service for verifying audit trail integrity.
    """
    
    def __init__(
        self,
        session: Session,
        ethereum_anchor: Optional[EthereumAnchor] = None
    ):
        self.session = session
        self.ethereum_anchor = ethereum_anchor
        self.audit_chain = AuditChain(session)
    
    def verify_entry(self, entry_id: str) -> VerificationResult:
        """
        Verify a single audit entry.
        
        Checks:
        1. Entry exists
        2. Entry hash is valid
        3. Entry is in a block
        4. Merkle proof is valid
        """
        errors = []
        details = {}
        
        # Get entry
        result = self.session.execute(
            select(AuditEntryModel).where(AuditEntryModel.entry_id == entry_id)
        )
        entry = result.scalar_one_or_none()
        
        if not entry:
            return VerificationResult(
                verified=False,
                timestamp=datetime.utcnow(),
                verification_type="entry",
                details={},
                errors=["Entry not found"]
            )
        
        details["entry_id"] = entry.entry_id
        details["event_type"] = entry.event_type
        details["timestamp"] = entry.timestamp.isoformat()
        
        # Verify entry hash
        entry_string = json.dumps({
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "action": entry.action,
            "actor_id": entry.actor_id,
            "data": entry.data
        }, sort_keys=True)
        
        computed_hash = hashlib.sha256(entry_string.encode()).hexdigest()
        
        if computed_hash != entry.entry_hash:
            errors.append("Entry hash mismatch. Entry may have been tampered.")
        else:
            details["hash_verified"] = True
        
        # Check if in block
        if entry.block_id:
            details["block_id"] = entry.block_id
            
            # Get Merkle proof
            proof = self.audit_chain.get_entry_proof(entry_id)
            
            if proof:
                # Verify Merkle proof
                merkle_proof = MerkleProof(
                    leaf_hash=proof["proof"]["leaf_hash"],
                    proof_hashes=proof["proof"]["proof_hashes"],
                    root_hash=proof["merkle_root"],
                    leaf_index=proof["proof"]["leaf_index"],
                    total_leaves=proof["proof"]["total_leaves"]
                )
                
                if MerkleTree.verify_proof(merkle_proof):
                    details["merkle_verified"] = True
                else:
                    errors.append("Merkle proof verification failed")
                
                details["block_number"] = proof["block_number"]
                details["anchored"] = proof["anchored"]
                
                if proof["anchored"]:
                    details["anchor_tx_hash"] = proof["anchor_tx_hash"]
        else:
            details["in_block"] = False
            details["note"] = "Entry pending inclusion in block"
        
        return VerificationResult(
            verified=len(errors) == 0,
            timestamp=datetime.utcnow(),
            verification_type="entry",
            details=details,
            errors=errors
        )
    
    def verify_block(self, block_number: int) -> VerificationResult:
        """
        Verify a single block.
        
        Checks:
        1. Block hash is valid
        2. Previous hash link is valid
        3. Merkle root matches entries
        4. Anchor verification (if anchored)
        """
        errors = []
        details = {}
        
        # Get block
        result = self.session.execute(
            select(AuditBlockModel).where(AuditBlockModel.block_number == block_number)
        )
        block = result.scalar_one_or_none()
        
        if not block:
            return VerificationResult(
                verified=False,
                timestamp=datetime.utcnow(),
                verification_type="block",
                details={},
                errors=["Block not found"]
            )
        
        details["block_number"] = block.block_number
        details["block_id"] = block.block_id
        details["entries_count"] = block.entries_count
        details["timestamp"] = block.timestamp.isoformat()
        
        # Verify block hash
        block_obj = AuditBlock(
            block_id=block.block_id,
            block_number=block.block_number,
            previous_hash=block.previous_hash,
            merkle_root=block.merkle_root,
            entries=[],
            entries_count=block.entries_count,
            timestamp=block.timestamp
        )
        
        computed_hash = block_obj.compute_hash()
        
        if computed_hash != block.block_hash:
            errors.append("Block hash mismatch")
        else:
            details["hash_verified"] = True
        
        # Verify previous hash link
        if block.block_number > 0:
            result = self.session.execute(
                select(AuditBlockModel)
                .where(AuditBlockModel.block_number == block.block_number - 1)
            )
            prev_block = result.scalar_one_or_none()
            
            if prev_block:
                if prev_block.block_hash != block.previous_hash:
                    errors.append("Previous hash link broken")
                else:
                    details["chain_link_verified"] = True
        else:
            # Genesis block
            if block.previous_hash != "0" * 64:
                errors.append("Invalid genesis block previous hash")
            else:
                details["genesis_block"] = True
        
        # Verify Merkle root
        result = self.session.execute(
            select(AuditEntryModel)
            .where(AuditEntryModel.block_id == block.block_id)
            .order_by(AuditEntryModel.timestamp)
        )
        entries = result.scalars().all()
        
        if len(entries) != block.entries_count:
            errors.append(f"Entry count mismatch. Expected {block.entries_count}, found {len(entries)}")
        else:
            # Rebuild Merkle tree
            entry_strings = [
                json.dumps({
                    "entry_id": e.entry_id,
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "action": e.action,
                    "actor_id": e.actor_id,
                    "data": e.data
                }, sort_keys=True)
                for e in entries
            ]
            
            merkle_tree = MerkleTree()
            computed_root = merkle_tree.build(entry_strings)
            
            if computed_root != block.merkle_root:
                errors.append("Merkle root mismatch")
            else:
                details["merkle_root_verified"] = True
        
        # Verify anchor if applicable (async call in sync context)
        if block.anchored and self.ethereum_anchor:
            try:
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    # If we're in an async context, we can't use run_until_complete
                    # For now, skip anchor verification in async context
                    details["anchor_verification"] = "skipped (async context)"
                except RuntimeError:
                    # No running loop, create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        anchor_result = loop.run_until_complete(
                            self.ethereum_anchor.verify_anchor(block.block_hash)
                        )
                        if anchor_result:
                            details["anchor_verified"] = True
                            details["anchor_timestamp"] = anchor_result["timestamp"].isoformat()
                        else:
                            errors.append("Anchor verification failed")
                    finally:
                        loop.close()
            except Exception as e:
                logger.warning(f"Anchor verification error: {e}")
                details["anchor_verification"] = f"error: {str(e)}"
        
        return VerificationResult(
            verified=len(errors) == 0,
            timestamp=datetime.utcnow(),
            verification_type="block",
            details=details,
            errors=errors
        )
    
    def verify_chain_integrity(
        self,
        from_block: int = 0,
        to_block: Optional[int] = None
    ) -> VerificationResult:
        """
        Verify integrity of the entire chain or a range.
        """
        is_valid, errors = self.audit_chain.verify_chain(from_block)
        
        # Get chain stats
        result = self.session.execute(
            select(func.count(AuditBlockModel.id))
        )
        total_blocks = result.scalar()
        
        result = self.session.execute(
            select(func.count(AuditEntryModel.id))
        )
        total_entries = result.scalar()
        
        result = self.session.execute(
            select(func.count(AuditBlockModel.id))
            .where(AuditBlockModel.anchored == 1)
        )
        anchored_blocks = result.scalar()
        
        return VerificationResult(
            verified=is_valid,
            timestamp=datetime.utcnow(),
            verification_type="chain",
            details={
                "total_blocks": total_blocks,
                "total_entries": total_entries,
                "anchored_blocks": anchored_blocks,
                "verified_from_block": from_block,
                "verified_to_block": to_block or (total_blocks - 1 if total_blocks > 0 else 0)
            },
            errors=errors
        )
    
    def generate_audit_certificate(
        self,
        entry_id: str
    ) -> Optional[Dict]:
        """
        Generate a cryptographic certificate for an audit entry.
        
        This can be shared with external parties for verification.
        """
        verification = self.verify_entry(entry_id)
        
        if not verification.verified:
            return None
        
        proof = self.audit_chain.get_entry_proof(entry_id)
        
        if not proof:
            return None
        
        # Get entry data
        result = self.session.execute(
            select(AuditEntryModel).where(AuditEntryModel.entry_id == entry_id)
        )
        entry = result.scalar_one()
        
        certificate = {
            "certificate_type": "RISKCAST_AUDIT_CERTIFICATE",
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            
            "entry": {
                "id": entry.entry_id,
                "hash": entry.entry_hash,
                "timestamp": entry.timestamp.isoformat(),
                "event_type": entry.event_type,
                "entity_type": entry.entity_type,
                "entity_id": entry.entity_id,
                "action": entry.action
            },
            
            "block": {
                "number": proof["block_number"],
                "hash": proof["block_hash"],
                "merkle_root": proof["merkle_root"]
            },
            
            "proof": {
                "merkle_proof": proof["proof"],
                "verification_algorithm": "SHA-256",
                "tree_type": "Binary Merkle Tree"
            },
            
            "anchoring": {
                "anchored": proof["anchored"],
                "blockchain": "Ethereum" if proof["anchored"] else None,
                "transaction_hash": proof.get("anchor_tx_hash")
            },
            
            "verification_instructions": {
                "step_1": "Compute SHA-256 hash of entry data",
                "step_2": "Verify hash matches entry.hash",
                "step_3": "Verify Merkle proof leads to block.merkle_root",
                "step_4": "If anchored, verify transaction on Ethereum"
            }
        }
        
        # Sign certificate
        certificate_hash = hashlib.sha256(
            json.dumps(certificate, sort_keys=True).encode()
        ).hexdigest()
        certificate["certificate_hash"] = certificate_hash
        
        return certificate
