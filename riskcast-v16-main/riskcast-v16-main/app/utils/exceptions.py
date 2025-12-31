from fastapi import status


class BaseAPIException(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "Bad request"

    def __init__(self, message: str = None):
        super().__init__(message or self.message)
        if message:
            self.message = message


class ValidationException(BaseAPIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "Validation failed"


class NotFoundException(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource not found"


class ServiceException(BaseAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Service error"




