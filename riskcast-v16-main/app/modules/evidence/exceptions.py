"""
Evidence Module Exceptions
Custom exceptions for evidence management
RISKCAST V3 - Modular Monolith
"""
from fastapi import HTTPException, status
from typing import Optional


class EvidenceNotFoundError(HTTPException):
    """Evidence object not found"""
    def __init__(self, evidence_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence object not found: {evidence_id}"
        )


class BundleNotFoundError(HTTPException):
    """Evidence bundle not found"""
    def __init__(self, bundle_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence bundle not found: {bundle_id}"
        )


class StorageError(HTTPException):
    """Storage operation failed"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage operation failed: {message}"
        )


class InvalidBundleManifestError(HTTPException):
    """Invalid bundle manifest"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid bundle manifest: {message}"
        )
