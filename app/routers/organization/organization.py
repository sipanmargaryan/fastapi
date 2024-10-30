from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.helpers import messages
from app.helpers.create_db import create_db
from app.helpers.database import get_db
from app.helpers.exceptions import PermissionDeniedError, ValidationError
from app.helpers.mail import send_mail
from app.helpers.middlewares import (
    is_logged_in_middleware,
    is_member_middleware,
    is_owner_middleware,
)
from app.helpers.response import Response
from app.routers.auth.crud import (
    create_user,
    get_active_user_by_email,
    get_active_user_by_id,
    get_user_by_email,
    get_user_by_id,
)
from app.routers.auth.schema import UserOrganizationCreationSchema
from app.routers.auth.utils import generate_auth_code, generate_tokens

from ...settings import FRONT_API
from ..admin.utils import create_organization_config_filesystem
from ..dashboard.schema import UserInfoSchema
from .crud import (
    check_invitation_code,
    check_user_in_organization,
    create_user_organization,
    del_user_organization,
    get_organization_users,
    insert_user_organization,
    refresh_invitation_info,
    user_organizations,
)
from .models import VerificationStatusTypes
from .schema import (
    AcceptSchema,
    OrganizationSchema,
    OrganizationUsersSchema,
    TeamInvitationSchema,
)

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("/{organization_id}/members")
async def organization_users_list(
    request: Request,
    organization_id: int,
    search: str = Query(default=""),
    db: Session = Depends(get_db),
    user_info: str = Depends(is_owner_middleware()),
):
    users = get_organization_users(organization_id, search, db)
    data = OrganizationUsersSchema(users=jsonable_encoder(users)).model_dump()
    return Response(data=data, message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/create-organization")
async def user_organization(
    data: UserOrganizationCreationSchema, db: Session = Depends(get_db)
):
    user_info = get_active_user_by_email(data.email, db)
    if user_info:
        raise ValidationError(messages.EMAIL_EXISTS)

    user = create_user_organization(db, data)
    create_db(data.domain)
    create_organization_config_filesystem(data.domain)

    await send_mail(
        subject=messages.EmailSubjects.ORGANIZATION_SUCCESSFULLY_CREATION,
        email_to=user.email,
        body=dict(),
        template="congrats",
    )

    data = generate_tokens(user)

    return Response(data=data, message=messages.SUCCESS, code=status.HTTP_201_CREATED)


@router.post("/team-invitation")
async def team_invitation(
    request: TeamInvitationSchema,
    db: Session = Depends(get_db),
    user_info: UserInfoSchema = Depends(is_owner_middleware()),
):
    verification_code = generate_auth_code()
    user = get_user_by_email(request.email, db)
    if user and user.active:
        user_in_organization = check_user_in_organization(
            user.id, user_info.organization_id, db
        )
        if user_in_organization:
            raise ValidationError(message=messages.USER_EXISTS)
        else:
            insert_user_organization(
                organization_id=user_info.organization_id,
                user_id=user.id,
                verification_status=VerificationStatusTypes.active,
                verification_code=None,
                db=db,
            )
            await send_mail(
                messages.EmailSubjects.VERIFICATION_CODE,
                user.email,
                dict(),
                "congrats",
            )
    elif user and not user.active:
        user_in_organization = check_user_in_organization(
            user.id, user_info.organization_id, db
        )
        refresh_invitation_info(user_in_organization, verification_code, db)
        await send_mail(
            messages.EmailSubjects.VERIFICATION_CODE,
            user.email,
            dict(
                auth_code_link=f"{FRONT_API}/invite-member?code={verification_code}",
            ),
            "verify_member",
        )
    else:
        user = create_user(db, email=request.email)
        insert_user_organization(
            user_info.organization_id,
            user.id,
            VerificationStatusTypes.pending,
            verification_code,
            db,
        )
        await send_mail(
            messages.EmailSubjects.VERIFICATION_CODE,
            user.email,
            dict(
                auth_code_link=f"{FRONT_API}/invite-member?code={verification_code}",
            ),
            "verify_member",
        )

    return Response(message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/accept-invitation")
async def accept_invitation(request: AcceptSchema, db: Session = Depends(get_db)):
    user_in_organization = check_invitation_code(request.code, db)
    data = dict(code=request.code)
    if user_in_organization:
        user = get_user_by_id(user_in_organization.user_id, db)
        data["email"] = user.email
        return Response(data=data, message=messages.SUCCESS, code=status.HTTP_200_OK)
    else:
        raise ValidationError(message=messages.INVALID_CODE)


@router.delete("/{organization_id}/members/{user_id}")
async def team_member_delete(
    user_id: int,
    organization_id: int,
    db: Session = Depends(get_db),
    user_info: UserInfoSchema = Depends(is_owner_middleware()),
):
    user = get_active_user_by_id(user_id, db)
    if not user:
        raise ValidationError(messages.ACCOUNT_NOT_FOUND)

    user_organization_instance = check_user_in_organization(
        user_id, organization_id, db
    )
    if not user_organization_instance:
        raise ValidationError(messages.USER_ORGANIZATION_NOT_FOUND)

    if user_id == user_info.user_id:
        raise PermissionDeniedError()
    del_user_organization(user_organization_instance, db)
    return Response(message=messages.DELETED, code=status.HTTP_202_ACCEPTED)


@router.get("/user-organizations-list")
async def user_organizations_list(
    user: UserInfoSchema = Depends(is_logged_in_middleware()),
    db: Session = Depends(get_db),
):
    data = user_organizations(user.id, db)
    organizations = OrganizationSchema(
        organizations=jsonable_encoder(data)
    ).model_dump()
    return Response(
        data=organizations["organizations"],
        message=messages.SUCCESS,
        code=status.HTTP_200_OK,
    )
