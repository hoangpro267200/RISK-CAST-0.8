"""
Blockchain-based Immutable Audit Trail

Features:
1. Merkle tree for efficient verification
2. Block-based audit chain
3. Public blockchain anchoring
4. Cryptographic verification
"""

from app.blockchain.merkle_tree import (
    MerkleTree,
    MerkleProof,
    IncrementalMerkleTree,
)

from app.blockchain.audit_chain import (
    AuditChain,
    AuditEntry,
    AuditBlock,
    AuditBlockModel,
    AuditEntryModel,
)

from app.blockchain.anchoring import (
    EthereumAnchor,
    BitcoinAnchor,
    AnchoringService,
)

from app.blockchain.verification import (
    VerificationService,
    VerificationResult,
)

__all__ = [
    "MerkleTree",
    "MerkleProof",
    "IncrementalMerkleTree",
    "AuditChain",
    "AuditEntry",
    "AuditBlock",
    "AuditBlockModel",
    "AuditEntryModel",
    "EthereumAnchor",
    "BitcoinAnchor",
    "AnchoringService",
    "VerificationService",
    "VerificationResult",
]
