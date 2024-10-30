from enum import Enum

from pydantic import BaseModel, WrapValidator, validate_email
from pydantic_core import PydanticCustomError
from typing_extensions import Annotated

from app.helpers.exceptions import ValidationError
from app.helpers.messages import INVALID_EMAIL


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
        return value

    return wrapper


EmailString = Annotated[
    str, WrapValidator(validate_email_format(ValidationError(INVALID_EMAIL)))
]


class UserInfoSchema(BaseModel):
    user_id: int
    organization_id: int
    last_name: str
    first_name: str
    business_phone_number: str
    user_type: str
    email: str


class DashboardItemSchema(BaseModel):
    id: int
    name: str
    pinned: bool


class DashboardListSchema(BaseModel):
    dashboards: list[DashboardItemSchema]


class DashboardPinSchema(BaseModel):
    dashboard_id: int


class DashboardRenameSchema(BaseModel):
    name: str
    dashboard_id: int


class ShareDashboardSchema(BaseModel):
    email: EmailString
    dashboard_id: int


class UserDashboardLastViewSchema(BaseModel):
    dashboard_id: int


class SortBy(str, Enum):
    name = "name"
    last_viewed = "last_viewed"
    oldest = "oldest"
    newest = "newest"


class DashboardMemberListSchema(BaseModel):
    user_id: int
    email: str
    first_name: str
    last_name: str
    image: str | None
