"""
Merkle Tree Implementation

Features:
1. Build tree from data
2. Generate proofs
3. Verify proofs
"""

import hashlib
from typing import List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class MerkleProof:
    """Merkle proof for verifying inclusion."""
    leaf_hash: str
    proof_hashes: List[Tuple[str, str]]  # (hash, position: 'left' or 'right')
    root_hash: str
    leaf_index: int
    total_leaves: int


class MerkleTree:
    """
    Merkle tree for efficient data verification.
    """
    
    def __init__(self, hash_function=None):
        self.hash_function = hash_function or self._sha256
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
        self.root: Optional[str] = None
    
    @staticmethod
    def _sha256(data: str) -> str:
        """SHA-256 hash function."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _hash_pair(self, left: str, right: str) -> str:
        """Hash a pair of nodes."""
        # Sort to ensure consistent ordering
        combined = left + right if left <= right else right + left
        return self.hash_function(combined)
    
    def build(self, data: List[str]) -> str:
        """
        Build Merkle tree from list of data items.
        
        Returns:
            Root hash of the tree
        """
        if not data:
            raise ValueError("Cannot build tree from empty data")
        
        # Hash all leaves
        self.leaves = [self.hash_function(item) for item in data]
        
        # Build tree bottom-up
        self.tree = [self.leaves.copy()]
        current_level = self.leaves.copy()
        
        while len(current_level) > 1:
            next_level = []
            
            # Pair up nodes and hash
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # If odd number of nodes, duplicate last one
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(self._hash_pair(left, right))
            
            self.tree.append(next_level)
            current_level = next_level
        
        self.root = current_level[0]
        return self.root
    
    def get_proof(self, index: int) -> MerkleProof:
        """
        Generate Merkle proof for item at given index.
        
        Args:
            index: Index of the leaf node
            
        Returns:
            MerkleProof object
        """
        if not self.tree:
            raise ValueError("Tree not built")
        
        if index < 0 or index >= len(self.leaves):
            raise IndexError(f"Index {index} out of range")
        
        proof_hashes = []
        current_index = index
        
        # Traverse up the tree
        for level in self.tree[:-1]:  # Exclude root level
            # Determine sibling
            if current_index % 2 == 0:
                # Current is left, sibling is right
                sibling_index = current_index + 1
                position = "right"
            else:
                # Current is right, sibling is left
                sibling_index = current_index - 1
                position = "left"
            
            # Get sibling hash (or self if at edge)
            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
            else:
                sibling_hash = level[current_index]  # Duplicate for odd count
            
            proof_hashes.append((sibling_hash, position))
            
            # Move to parent index
            current_index = current_index // 2
        
        return MerkleProof(
            leaf_hash=self.leaves[index],
            proof_hashes=proof_hashes,
            root_hash=self.root,
            leaf_index=index,
            total_leaves=len(self.leaves)
        )
    
    @classmethod
    def verify_proof(cls, proof: MerkleProof) -> bool:
        """
        Verify a Merkle proof.
        
        Args:
            proof: MerkleProof to verify
            
        Returns:
            True if proof is valid
        """
        current_hash = proof.leaf_hash
        
        for sibling_hash, position in proof.proof_hashes:
            if position == "left":
                current_hash = cls._sha256(sibling_hash + current_hash)
            else:
                current_hash = cls._sha256(current_hash + sibling_hash)
        
        return current_hash == proof.root_hash
    
    def get_root(self) -> Optional[str]:
        """Get the root hash."""
        return self.root
    
    def to_dict(self) -> dict:
        """Serialize tree to dictionary."""
        return {
            "leaves": self.leaves,
            "root": self.root,
            "tree_levels": len(self.tree),
            "total_leaves": len(self.leaves)
        }


class IncrementalMerkleTree:
    """
    Merkle tree that supports incremental additions.
    Optimized for append-only audit logs.
    """
    
    def __init__(self, max_depth: int = 32):
        self.max_depth = max_depth
        self.leaves: List[str] = []
        self.filled_subtrees: List[str] = ["0" * 64] * max_depth
        self.root: str = "0" * 64
        self.zeros = self._compute_zeros()
    
    @staticmethod
    def _sha256(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _compute_zeros(self) -> List[str]:
        """Compute zero hashes for each level."""
        zeros = ["0" * 64]
        for _ in range(self.max_depth - 1):
            zeros.append(self._sha256(zeros[-1] + zeros[-1]))
        return zeros
    
    def append(self, data: str) -> Tuple[str, int]:
        """
        Append a new leaf and return new root and index.
        
        Args:
            data: Data to add
            
        Returns:
            Tuple of (new_root, leaf_index)
        """
        leaf_hash = self._sha256(data)
        self.leaves.append(leaf_hash)
        
        leaf_index = len(self.leaves) - 1
        current_hash = leaf_hash
        current_index = leaf_index
        
        for level in range(self.max_depth):
            if current_index % 2 == 0:
                # Left child, store and use zero for right
                self.filled_subtrees[level] = current_hash
                current_hash = self._sha256(current_hash + self.zeros[level])
            else:
                # Right child, combine with stored left
                current_hash = self._sha256(self.filled_subtrees[level] + current_hash)
            
            current_index = current_index // 2
        
        self.root = current_hash
        return self.root, leaf_index
    
    def get_root(self) -> str:
        """Get current root hash."""
        return self.root
    
    def get_leaf_count(self) -> int:
        """Get number of leaves."""
        return len(self.leaves)
