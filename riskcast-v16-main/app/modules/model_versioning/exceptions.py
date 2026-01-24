"""
Model Versioning Exceptions
Custom exceptions for model versioning module
RISKCAST V3 - Modular Monolith
"""
from fastapi import HTTPException, status
from typing import Optional


class ModelVersionNotFoundError(HTTPException):
    """Model version not found"""
    def __init__(self, model_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version not found: {model_id}"
        )


class ModelAlreadyPublishedError(HTTPException):
    """Model version is already published"""
    def __init__(self, model_id: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model version {model_id} is already published and cannot be modified"
        )


class ModelImmutableError(HTTPException):
    """Attempt to modify immutable published model"""
    def __init__(self, model_id: str, message: str = "Cannot modify published model"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model version {model_id}: {message}"
        )


class ActivationNotFoundError(HTTPException):
    """Model activation not found"""
    def __init__(self, activation_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model activation not found: {activation_id}"
        )


class NoActiveModelError(HTTPException):
    """No active model found for given criteria"""
    def __init__(self, product_type: str, corridor_id: Optional[str] = None):
        message = f"No active model found for product_type={product_type}"
        if corridor_id:
            message += f", corridor_id={corridor_id}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class InvalidModelScopeError(HTTPException):
    """Invalid model scope"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message
        )


class ModelVersionExistsError(HTTPException):
    """Model version with same name and version already exists"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )


class DuplicateModelError(HTTPException):
    """Model with identical parameters already exists"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )


class InvalidModelStateError(HTTPException):
    """Invalid model state for operation"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )
