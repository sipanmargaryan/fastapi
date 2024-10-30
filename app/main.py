from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from .helpers.exceptions import (
    MethodNotAllowed,
    NotFound,
    ServiceException,
    ValidationError,
)
from .routers.admin import admin
from .routers.auth import auth
from .routers.dashboard import dashboard
from .routers.organization import organization

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(organization.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.exception_handler(HTTP_404_NOT_FOUND)
async def not_found_handler(request: Request, exc: NotFound):
    return NotFound().to_response()


@app.exception_handler(HTTP_500_INTERNAL_SERVER_ERROR)
async def internal_server_error_handler(request: Request, exc: ServiceException):
    return ServiceException().to_response()


@app.exception_handler(HTTP_405_METHOD_NOT_ALLOWED)
async def method_not_allowed_handler(request: Request, exc: MethodNotAllowed):
    return MethodNotAllowed().to_response()


@app.exception_handler(RequestValidationError)
async def unprocessable_entity_handler(request: Request, exc: ValidationError):
    return ValidationError(status_code=HTTP_422_UNPROCESSABLE_ENTITY).to_response()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return True
