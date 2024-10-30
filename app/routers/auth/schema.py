import enum

from pydantic import BaseModel, Field, WrapValidator, validate_email
from pydantic_core import PydanticCustomError
from typing_extensions import Annotated

from app.helpers.exceptions import AuthenticationFailedError, ValidationError
from app.helpers.messages import INVALID_DOMAIN, INVALID_EMAIL, INVALID_PASSWORD

from ..organization.models import UserTypes
from .models import AdminTypes
from .utils import is_valid_password, is_valid_subdomain


class CompanySizeTypes(enum.Enum):
    small = "1 to 5"
    medium = "6 to 20"
    large = "21 to 100"
    extra_large = "More than 100"


def validate_email_format(error_class):
    def wrapper(value, handler):
        """CUSTOM FUNCTION TO VALIDATE EMAIL FORMAT
        Raises ValidationError if email is not valid for EmailString
        Raises AuthenticationFailedError if email is not valid for LoginEmailString
        """
        try:
            validate_email(value)
        except PydanticCustomError:
            raise error_class
        return value.lower()

    return wrapper


def validate_password_format(value, handler):
    if not is_valid_password(value):
        raise ValidationError(INVALID_PASSWORD)

    return value


def validate_domain_format(value, handler):
    if not is_valid_subdomain(value):
        raise ValidationError(INVALID_DOMAIN)

    return value


EmailString = Annotated[
    str, WrapValidator(validate_email_format(ValidationError(INVALID_EMAIL)))
]
PasswordString = Annotated[str, WrapValidator(validate_password_format)]
LoginEmailString = Annotated[
    str, WrapValidator(validate_email_format(AuthenticationFailedError))
]
DomainString = Annotated[str, WrapValidator(validate_domain_format)]


class UserSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailString


class UserOrganizationInfoSchema(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailString
    business_phone_number: str
    user_type: UserTypes


class UserInfoSchema(UserSchema):
    id: int = Field(..., alias="user_id")
    business_phone_number: str


class UserLoginSchema(BaseModel):
    email: LoginEmailString
    password: str


class UserEmailRegistrationSchema(BaseModel):
    email: EmailString


class UserPasswordSchema(BaseModel):
    email: EmailString
    password: PasswordString


class ForgotPasswordSchema(BaseModel):
    email: EmailString


class ResetPasswordSchema(BaseModel):
    password: PasswordString
    code: str


class ResetPasswordCodeSchema(BaseModel):
    code: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class AuthCodeValidationSchema(BaseModel):
    code: str


class CountrySchema(BaseModel):
    name: str
    dial_code: str
    code: str
    id: int


class CountryListSchema(BaseModel):
    data: list[CountrySchema]


class UserOrganizationCreationSchema(BaseModel):
    auth_code: str | None = None
    first_name: str
    last_name: str
    business_phone_number: str
    country_or_region: int
    company_name: str
    company_size: CompanySizeTypes
    domain: str
    password: PasswordString | None = None
    email: EmailString


class DomainValidateSchema(BaseModel):
    domain: DomainString


class ProviderEnum(enum.Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class SocialSignUpSchema(BaseModel):
    code: str
    provider: ProviderEnum


class TeamMemberSignUpSchema(BaseModel):
    email: EmailString
    code: str
    first_name: str
    last_name: str
    password: PasswordString


class UserTokenPayload(BaseModel):
    user_id: int
    email: EmailString
    first_name: str
    last_name: str
    admin_type: AdminTypes | None
