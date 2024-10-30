from fastapi import APIRouter, Depends, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.helpers import messages
from app.helpers.database import get_db
from app.helpers.exceptions import (
    AuthenticationFailedError,
    PermissionDeniedError,
    RequestError,
    ValidationError,
)
from app.helpers.jwt import jwt_decode
from app.helpers.mail import send_mail
from app.helpers.oauth import get_user_info_from_provider
from app.helpers.response import Response
from app.settings import FRONT_API

from ...helpers.middlewares import is_logged_in_middleware, is_member_middleware
from ..dashboard.utils import split_domain
from ..organization.crud import refresh_verification_status
from ..organization.models import UserTypes, VerificationStatusTypes
from ..organization.schema import AcceptSchema
from .crud import (
    check_user_reset_password_code,
    check_verification_code,
    create_team_member,
    create_user,
    get_active_user_by_email,
    get_country,
    get_domain,
    get_user_and_organization_by_domain_name,
    get_user_by_auth_code,
    get_user_by_email,
    update_auth_code,
    update_reset_pass_code,
    update_user_password,
)
from .schema import (
    AuthCodeValidationSchema,
    CountryListSchema,
    DomainValidateSchema,
    ForgotPasswordSchema,
    RefreshTokenSchema,
    ResetPasswordCodeSchema,
    ResetPasswordSchema,
    SocialSignUpSchema,
    TeamMemberSignUpSchema,
    UserEmailRegistrationSchema,
    UserInfoSchema,
    UserLoginSchema,
    UserOrganizationInfoSchema,
)
from .utils import (
    generate_auth_code,
    generate_reset_code,
    generate_tokens,
    get_timedelta_from_hours,
    verify_password,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.post("/sign-up")
async def sign_up(user: UserEmailRegistrationSchema, db: Session = Depends(get_db)):
    user_info = get_user_by_email(user.email, db)
    auth_code = generate_auth_code()
    if user_info and user_info.active:
        # EXISTING USER WITH VERIFICATION
        raise ValidationError(messages.EMAIL_EXISTS)

    if not user_info:
        # NEW USER
        user = create_user(db, email=user.email, auth_code=auth_code)

    if user_info and user_info.auth_code and not user_info.active:
        # EXISTING USER WITHOUT VERIFICATION
        update_auth_code(user.email, auth_code, db)

    await send_mail(
        messages.EmailSubjects.VERIFICATION_CODE,
        user.email,
        dict(
            auth_code_link=f"{FRONT_API}/sign-up?code={auth_code}",  # issue with query param
        ),
        "verify",
    )
    return Response(message=messages.SUCCESS, code=status.HTTP_201_CREATED)


@router.post("/sign-in")
async def sign_in(user_data: UserLoginSchema, db: Session = Depends(get_db)):
    user = get_active_user_by_email(user_data.email, db)
    if user is None:
        raise AuthenticationFailedError()
    if not verify_password(user_data.password, user.password):
        raise AuthenticationFailedError()

    data = generate_tokens(user)

    return Response(data=data, message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordSchema, db: Session = Depends(get_db)):
    user = get_active_user_by_email(request.email, db)
    if not user:
        raise ValidationError(messages.EMAIL_NOT_EXISTS)

    reset_pass_code = generate_reset_code()
    reset_pass_code_expiration_date = get_timedelta_from_hours(hours=1)

    user = update_reset_pass_code(
        user, reset_pass_code, reset_pass_code_expiration_date, db
    )

    await send_mail(
        messages.EmailSubjects.FORGOT_PASSWORD,
        user.email,
        dict(
            content="ankap maila mi xarnvi irar",
            recipient="User User",
            subject="shoq exanakin arevi tak petq chi kangnel",
            reset_pass_code=f"{reset_pass_code}",  # issue with reset_pass_link
        ),
        "forgot",
    )
    return Response(
        data=dict(email=user.email), message=messages.SUCCESS, code=status.HTTP_200_OK
    )


@router.post("/verify-reset-password-code")
async def verify_reset_password_code(
    request: ResetPasswordCodeSchema, db: Session = Depends(get_db)
):
    user = check_user_reset_password_code(request.code, db)
    if not user:
        raise ValidationError(messages.INVALID_CODE)

    return Response(message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.patch("/reset-password")
async def reset_password(request: ResetPasswordSchema, db: Session = Depends(get_db)):
    user = check_user_reset_password_code(request.code, db)
    if not user:
        raise ValidationError(messages.INVALID_CODE)

    update_user_password(user, request.password, db)

    return Response(message=messages.SUCCESS, code=status.HTTP_204_NO_CONTENT)


@router.post("/refresh-token")
async def refresh_token(request: RefreshTokenSchema, db: Session = Depends(get_db)):
    user = jwt_decode(request.refresh_token)
    user = get_active_user_by_email(user["email"], db)
    data = generate_tokens(user, request.refresh_token)

    return Response(
        data=data, message=messages.SUCCESS, code=status.HTTP_204_NO_CONTENT
    )


@router.post("/check-user-by-auth-code")
async def check_user_by_auth_code(
    request: AuthCodeValidationSchema, db: Session = Depends(get_db)
):
    user = get_user_by_auth_code(request.code, db)
    if not user:
        raise ValidationError(messages.INVALID_CODE)

    return Response(
        data=dict(email=user.email),
        message=messages.SUCCESS,
        code=status.HTTP_204_NO_CONTENT,
    )


@router.get("/countries")
async def country(db: Session = Depends(get_db)):
    country_list = get_country(db)
    countries = CountryListSchema(data=jsonable_encoder(country_list)).model_dump()
    return Response(
        data=countries["data"], message=messages.SUCCESS, code=status.HTTP_200_OK
    )


@router.post("/validate-subdomain")
async def validate_subdomain(
    request: DomainValidateSchema, db: Session = Depends(get_db)
):
    domain = get_domain(request.domain, db)
    if domain:
        raise ValidationError(messages.DOMAIN_EXISTS)
    return Response(message=messages.SUCCESS, code=status.HTTP_204_NO_CONTENT)


@router.post("/oauth/sign-up")
async def social_sign_up(request: SocialSignUpSchema, db: Session = Depends(get_db)):
    info = await get_user_info_from_provider(
        request.provider,
        request.code,
    )
    if get_active_user_by_email(info["email"], db):
        # ALREADY VERIFIED USER
        raise ValidationError(messages.EMAIL_EXISTS)
    if get_user_by_email(info["email"], db):
        # ALREADY EXISTING USER WITHOUT VERIFICATION
        return Response(data=info, message=messages.SUCCESS, code=status.HTTP_200_OK)
    user = create_user(
        db,
        email=info["email"],
        first_name=info["first_name"],
        last_name=info["last_name"],
    )
    return Response(data=info, message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/oauth/sign-in")
async def social_sign_in(request: SocialSignUpSchema, db: Session = Depends(get_db)):
    info = await get_user_info_from_provider(
        request.provider,
        request.code,
    )
    user = get_active_user_by_email(info["email"], db)
    if user:
        data = generate_tokens(user)
        return Response(data=data, message=messages.SUCCESS, code=status.HTTP_200_OK)
    raise AuthenticationFailedError()


@router.get("/me")
async def me(user_info=Depends(is_logged_in_middleware())):
    user_info = UserInfoSchema(
        user_id=user_info.id,
        email=user_info.email,
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        business_phone_number=user_info.business_phone_number,
    ).model_dump()
    return Response(data=user_info, message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.get("/user-organization")
async def user_organization(
    request: Request,
    db: Session = Depends(get_db),
    user_info=Depends(is_member_middleware()),
):
    host = split_domain(request.headers.get("referer"))
    organization_by_domain = get_user_and_organization_by_domain_name(
        user_info.user_id, host, db
    )
    if not organization_by_domain:
        raise AuthenticationFailedError()
    user_info = UserOrganizationInfoSchema(**organization_by_domain).model_dump()
    return Response(data=user_info, message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/team-member-sign-up")
async def team_member_sign_up(
    data: TeamMemberSignUpSchema, db: Session = Depends(get_db)
):
    user = get_user_by_email(data.email, db)
    user_in_organization = check_verification_code(
        user.id, data.code, VerificationStatusTypes.pending, db
    )
    if not user_in_organization:
        raise RequestError(messages.USER_ORGANIZATION_NOT_FOUND)

    refresh_verification_status(user.id, db)

    create_team_member(db, data, user, user_in_organization)

    return Response(
        message=messages.SUCCESS,
        code=status.HTTP_204_NO_CONTENT,
    )
