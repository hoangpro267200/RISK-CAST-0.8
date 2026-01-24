"""
Risk Assessments Module Exceptions
RISKCAST V3 - Modular Monolith
"""
from app.shared.exceptions import NotFoundError, ValidationError


class AssessmentNotFoundError(NotFoundError):
    """Raised when risk assessment is not found"""
    
    def __init__(self, assessment_id: str):
        super().__init__("RiskAssessment", assessment_id)
        self.assessment_id = assessment_id


class AssessmentValidationError(ValidationError):
    """Raised when risk assessment validation fails"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


class DuplicateAssessmentError(ValidationError):
    """Raised when attempting to create duplicate assessment (same input hash)"""
    
    def __init__(self, input_hash: str, existing_assessment_id: str):
        super().__init__(
            f"Assessment with input hash {input_hash} already exists (ID: {existing_assessment_id})"
        )
        self.input_hash = input_hash
        self.existing_assessment_id = existing_assessment_id
