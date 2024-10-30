from fastapi import Depends, Header
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.helpers.database import get_db
from app.helpers.exceptions import PermissionDeniedError
from app.helpers.jwt import jwt_decode
from app.routers.admin.crud import get_active_admin_by_email
from app.routers.auth.crud import (
    get_active_user_by_id,
    get_user_and_organization_by_domain_name,
)
from app.routers.auth.models import AdminTypes
from app.routers.auth.schema import UserTokenPayload
from app.routers.dashboard.schema import UserInfoSchema
from app.routers.dashboard.utils import split_domain
from app.routers.organization.models import UserTypes


def is_admin_middleware():
    async def middleware(
        Authorization: str = Header(...), db: Session = Depends(get_db)
    ):
        consultant_token_info: UserTokenPayload = UserTokenPayload(
            **jwt_decode(Authorization)
        )
        consultant_info = get_active_admin_by_email(
            consultant_token_info.email, AdminTypes.consultant, db
        )
        if consultant_info is None:
            raise PermissionDeniedError()
        return consultant_token_info

    return middleware


def check_user_info_by_token(access_token, domain, db):
    user_token_info: UserTokenPayload = UserTokenPayload(**jwt_decode(access_token))
    user_organization_info = get_user_and_organization_by_domain_name(
        user_token_info.user_id, domain, db
    )
    if user_organization_info is None:
        raise PermissionDeniedError()
    return UserInfoSchema(**user_organization_info)


def is_owner_middleware():
    async def middleware(
        request: Request,
        Authorization: str = Header(...),
        db: Session = Depends(get_db),
    ):
        user_organization_info: UserInfoSchema = check_user_info_by_token(
            Authorization, split_domain(request.headers.get("referer")), db
        )
        if user_organization_info.user_type != UserTypes.owner:
            raise PermissionDeniedError()
        return user_organization_info

    return middleware


def is_member_middleware(only_members: bool = False):
    async def middleware(
        request: Request,
        Authorization: str = Header(...),
        db: Session = Depends(get_db),
    ):
        user_organization_info: UserInfoSchema = check_user_info_by_token(
            Authorization, split_domain(request.headers.get("referer")), db
        )
        if not only_members:
            return user_organization_info
        if user_organization_info.user_type != UserTypes.member:
            raise PermissionDeniedError()
        return user_organization_info

    return middleware


def is_super_user_middleware():
    async def middleware(
        Authorization: str = Header(...), db: Session = Depends(get_db)
    ):
        super_user_token_info: UserTokenPayload = UserTokenPayload(
            **jwt_decode(Authorization)
        )
        super_user_info = get_active_admin_by_email(
            super_user_token_info.email, AdminTypes.superuser, db
        )
        if super_user_info is None:
            raise PermissionDeniedError()
        return super_user_token_info

    return middleware


def is_logged_in_middleware():
    async def middleware(
        Authorization: str = Header(...), db: Session = Depends(get_db)
    ):
        user_token_info: UserTokenPayload = UserTokenPayload(
            **jwt_decode(Authorization)
        )
        user_info = get_active_user_by_id(user_token_info.user_id, db)
        if not user_info:
            raise PermissionDeniedError()
        return user_info

    return middleware
