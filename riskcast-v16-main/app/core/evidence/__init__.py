"""
Evidence Core Module
Storage abstraction and utilities for evidence management.
"""
from app.core.evidence.storage import EvidenceStorage, LocalEvidenceStorage, S3EvidenceStorage

__all__ = [
    'EvidenceStorage',
    'LocalEvidenceStorage',
    'S3EvidenceStorage',
]
