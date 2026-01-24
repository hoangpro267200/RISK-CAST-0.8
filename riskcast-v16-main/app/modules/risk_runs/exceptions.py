"""
Risk Runs Module Exceptions
RISKCAST V3 - Modular Monolith
"""
from app.shared.exceptions import NotFoundError, ValidationError


class RunNotFoundError(NotFoundError):
    """Raised when risk run is not found"""
    
    def __init__(self, run_id: str):
        super().__init__("RiskRun", run_id)
        self.run_id = run_id


class RunValidationError(ValidationError):
    """Raised when risk run validation fails"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


class RunExecutionError(ValidationError):
    """Raised when risk run execution fails"""
    
    def __init__(self, message: str, run_id: str = None):
        super().__init__(message)
        self.run_id = run_id
