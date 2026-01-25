"""
Blockchain-based Audit Chain

Features:
1. Immutable audit blocks
2. Chain integrity verification
3. Periodic anchoring
"""

import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Text, update, JSON, Index
from sqlalchemy.orm import Session
from sqlalchemy import select

# JSONB fallback for PostgreSQL
try:
    from sqlalchemy.dialects.postgresql import JSONB
    JSONType = JSONB
except (ImportError, AttributeError):
    JSONType = JSON

from app.blockchain.merkle_tree import MerkleTree, MerkleProof
from app.core.logging import get_logger
from app.database import Base


logger = get_logger(__name__)


@dataclass
class AuditEntry:
    """Single audit entry."""
    entry_id: str
    timestamp: datetime
    event_type: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    actor_type: str  # "user", "system", "api"
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_hashable_string(self) -> str:
        """Convert to deterministic string for hashing."""
        return json.dumps({
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "data": self.data
        }, sort_keys=True)


@dataclass
class AuditBlock:
    """Block containing multiple audit entries."""
    block_id: str
    block_number: int
    previous_hash: str
    merkle_root: str
    entries: List[AuditEntry]
    entries_count: int
    timestamp: datetime
    block_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute block hash."""
        content = json.dumps({
            "block_id": self.block_id,
            "block_number": self.block_number,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "entries_count": self.entries_count,
            "timestamp": self.timestamp.isoformat()
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class AuditBlockModel(Base):
    """Database model for audit blocks."""
    __tablename__ = "audit_blocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    block_id = Column(String(36), unique=True, nullable=False, index=True)
    block_number = Column(Integer, unique=True, nullable=False, index=True)
    previous_hash = Column(String(64), nullable=False)
    merkle_root = Column(String(64), nullable=False)
    entries_count = Column(Integer, nullable=False)
    entries_data = Column(JSONType, nullable=False)
    block_hash = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    anchored = Column(Integer, default=0, index=True)  # Boolean as integer
    anchor_tx_hash = Column(String(66), index=True)  # Ethereum tx hash
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_audit_blocks_anchored', 'anchored'),
        Index('ix_audit_blocks_timestamp', 'timestamp'),
    )


class AuditEntryModel(Base):
    """Database model for individual audit entries."""
    __tablename__ = "audit_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(36), unique=True, nullable=False, index=True)
    block_id = Column(String(36), index=True)  # Null until included in block
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    actor_id = Column(String(36), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False)
    data = Column(JSONType, nullable=False)
    metadata = Column(JSONType, default={})
    entry_hash = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_audit_entries_block', 'block_id'),
        Index('ix_audit_entries_entity', 'entity_type', 'entity_id'),
        Index('ix_audit_entries_actor', 'actor_type', 'actor_id'),
        Index('ix_audit_entries_timestamp', 'timestamp'),
    )


class AuditChain:
    """
    Manages the blockchain-based audit trail.
    """
    
    GENESIS_HASH = "0" * 64
    BLOCK_SIZE = 100  # Entries per block
    
    def __init__(self, session: Session):
        self.session = session
        self.pending_entries: List[AuditEntry] = []
    
    def log_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        action: str,
        actor_id: str,
        actor_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an audit event.
        
        Returns:
            Entry ID
        """
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            data=data,
            metadata=metadata or {}
        )
        
        entry_hash = hashlib.sha256(entry.to_hashable_string().encode()).hexdigest()
        
        # Store in database
        entry_model = AuditEntryModel(
            entry_id=entry.entry_id,
            event_type=entry.event_type,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            action=entry.action,
            actor_id=entry.actor_id,
            actor_type=entry.actor_type,
            data=entry.data,
            metadata=entry.metadata,
            entry_hash=entry_hash,
            timestamp=entry.timestamp
        )
        
        self.session.add(entry_model)
        self.session.flush()
        
        self.pending_entries.append(entry)
        
        # Check if we should create a new block
        if len(self.pending_entries) >= self.BLOCK_SIZE:
            self.create_block()
        
        logger.debug(f"Audit entry logged: {entry.entry_id}")
        return entry.entry_id
    
    def create_block(self) -> Optional[AuditBlock]:
        """
        Create a new block from pending entries.
        """
        if not self.pending_entries:
            return None
        
        # Get previous block
        result = self.session.execute(
            select(AuditBlockModel)
            .order_by(AuditBlockModel.block_number.desc())
            .limit(1)
        )
        previous_block = result.scalar_one_or_none()
        
        previous_hash = previous_block.block_hash if previous_block else self.GENESIS_HASH
        block_number = (previous_block.block_number + 1) if previous_block else 0
        
        # Build Merkle tree from entries
        entry_strings = [e.to_hashable_string() for e in self.pending_entries]
        merkle_tree = MerkleTree()
        merkle_root = merkle_tree.build(entry_strings)
        
        # Create block
        block = AuditBlock(
            block_id=str(uuid.uuid4()),
            block_number=block_number,
            previous_hash=previous_hash,
            merkle_root=merkle_root,
            entries=self.pending_entries.copy(),
            entries_count=len(self.pending_entries),
            timestamp=datetime.utcnow()
        )
        block.block_hash = block.compute_hash()
        
        # Store block
        block_model = AuditBlockModel(
            block_id=block.block_id,
            block_number=block.block_number,
            previous_hash=block.previous_hash,
            merkle_root=block.merkle_root,
            entries_count=block.entries_count,
            entries_data=[{
                "entry_id": e.entry_id,
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "action": e.action,
                "timestamp": e.timestamp.isoformat()
            } for e in block.entries],
            block_hash=block.block_hash,
            timestamp=block.timestamp
        )
        
        self.session.add(block_model)
        
        # Update entries with block_id
        for entry in self.pending_entries:
            self.session.execute(
                update(AuditEntryModel)
                .where(AuditEntryModel.entry_id == entry.entry_id)
                .values(block_id=block.block_id)
            )
        
        self.session.flush()
        
        # Clear pending entries
        self.pending_entries = []
        
        logger.info(
            f"Audit block created: {block.block_number}",
            extra={
                "block_id": block.block_id,
                "entries_count": block.entries_count
            }
        )
        
        return block
    
    def verify_chain(self, from_block: int = 0) -> Tuple[bool, List[str]]:
        """
        Verify integrity of the audit chain.
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        result = self.session.execute(
            select(AuditBlockModel)
            .where(AuditBlockModel.block_number >= from_block)
            .order_by(AuditBlockModel.block_number)
        )
        blocks = result.scalars().all()
        
        if not blocks:
            return True, []
        
        previous_hash = self.GENESIS_HASH
        if from_block > 0:
            # Get hash of previous block
            prev_result = self.session.execute(
                select(AuditBlockModel)
                .where(AuditBlockModel.block_number == from_block - 1)
            )
            prev_block = prev_result.scalar_one_or_none()
            if prev_block:
                previous_hash = prev_block.block_hash
        
        for block in blocks:
            # Verify previous hash link
            if block.previous_hash != previous_hash:
                errors.append(
                    f"Block {block.block_number}: Invalid previous hash. "
                    f"Expected {previous_hash[:16]}..., got {block.previous_hash[:16]}..."
                )
            
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
                errors.append(
                    f"Block {block.block_number}: Block hash mismatch. "
                    f"Computed {computed_hash[:16]}..., stored {block.block_hash[:16]}..."
                )
            
            previous_hash = block.block_hash
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Chain verification passed. {len(blocks)} blocks verified.")
        else:
            logger.warning(f"Chain verification failed. {len(errors)} errors found.")
        
        return is_valid, errors
    
    def get_entry_proof(self, entry_id: str) -> Optional[Dict]:
        """
        Get Merkle proof for an audit entry.
        """
        # Get entry and its block
        result = self.session.execute(
            select(AuditEntryModel)
            .where(AuditEntryModel.entry_id == entry_id)
        )
        entry = result.scalar_one_or_none()
        
        if not entry or not entry.block_id:
            return None
        
        # Get all entries in the block
        result = self.session.execute(
            select(AuditEntryModel)
            .where(AuditEntryModel.block_id == entry.block_id)
            .order_by(AuditEntryModel.timestamp)
        )
        block_entries = result.scalars().all()
        
        # Find entry index
        entry_index = None
        for i, e in enumerate(block_entries):
            if e.entry_id == entry_id:
                entry_index = i
                break
        
        if entry_index is None:
            return None
        
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
            for e in block_entries
        ]
        
        merkle_tree = MerkleTree()
        merkle_tree.build(entry_strings)
        
        proof = merkle_tree.get_proof(entry_index)
        
        # Get block info
        result = self.session.execute(
            select(AuditBlockModel)
            .where(AuditBlockModel.block_id == entry.block_id)
        )
        block = result.scalar_one()
        
        return {
            "entry_id": entry_id,
            "block_number": block.block_number,
            "block_hash": block.block_hash,
            "merkle_root": block.merkle_root,
            "proof": {
                "leaf_hash": proof.leaf_hash,
                "proof_hashes": proof.proof_hashes,
                "leaf_index": proof.leaf_index,
                "total_leaves": proof.total_leaves
            },
            "anchored": bool(block.anchored),
            "anchor_tx_hash": block.anchor_tx_hash
        }
