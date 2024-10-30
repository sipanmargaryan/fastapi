import dataclasses
from dataclasses import asdict

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.helpers import messages


class ServiceException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = messages.ERROR
    code = "INTERNAL_SERVER_ERROR"
    meta = {}

    def __init__(
        self, message=None, code=None, errors=None, status_code=None, meta=None
    ):
        print(status_code)
        if meta:
            self.meta = meta

        if message:
            self.message = message
        if status_code:
            self.status_code = status_code

        self.payload = {"message": self.message}

        if errors:
            self.payload["errors"] = errors

        if code:
            self.code = code

        if self.code:
            self.payload["code"] = self.code

        super().__init__(status_code=self.status_code, detail=self.payload)

    def to_response(self, is_json=True):
        return (
            JSONResponse(
                status_code=self.status_code,
                content={
                    "detail": {i: v for i, v in self.payload.items() if v is not None}
                },
            )
            if is_json
            else dict(detail=self.payload)
        )


class RequestError(ServiceException):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Bad request"
    code = "BAD_REQUEST"


class AuthenticationFailedError(ServiceException):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Authentication Failed."
    code = "AUTHENTICATION_FAILED"


class JWTTokenError(AuthenticationFailedError):
    message = "Invalid JWT Token."
    code = "JWT_TOKEN_ERROR"


class JWTInvalidTokenError(JWTTokenError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "JWT_INVALID_TOKEN"


class JWTExpiredSignatureError(JWTTokenError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Expired JWT Signature."
    code = "JWT_EXPIRED_TOKEN"


class PermissionDeniedError(ServiceException):
    status_code = status.HTTP_403_FORBIDDEN
    message = "You do not have permission to perform this action."
    code = "PERMISSION_DENIED"


class ValidationError(ServiceException):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Validation Error"
    code = "VALIDATION_ERROR"


class MethodNotAllowed(ServiceException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    message = "Method Not Allowed"
    code = "METHOD_NOT_ALLOWED"


class NotFound(ServiceException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Not Found"
    code = "NOT_FOUND"


class MeltanoError(ServiceException):
    status_code = status.HTTP_409_CONFLICT
    message = "Meltano Error"
    code = "MELTANO_ERROR"
