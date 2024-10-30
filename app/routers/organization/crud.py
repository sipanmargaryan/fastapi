from typing import List, Union

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.helpers import messages
from app.helpers.exceptions import ValidationError
from app.routers.auth.models import User
from app.routers.auth.schema import UserOrganizationCreationSchema
from app.routers.auth.utils import get_password_hash

from ..auth.crud import get_user_by_auth_code, get_user_by_email
from .models import Organization, UserOrganization, UserTypes, VerificationStatusTypes


def insert_data(db: Session, instance):
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def get_organization_users(
    organization_id: int, search: str, db: Session
) -> Union[List[User], List]:
    users_in_organization = (
        db.query(User)
        .join(UserOrganization, UserOrganization.user_id == User.id)
        .filter(
            UserOrganization.organization_id == organization_id,
            UserOrganization.verification_status == VerificationStatusTypes.active,
            User.active == True,
        )
    )
    if search:
        search = f"%{search}%"
        users_in_organization = users_in_organization.filter(
            or_(
                User.email.ilike(search),
                User.first_name.ilike(search),
                User.last_name.ilike(search),
            )
        )
    return users_in_organization.all()


def create_user_organization(
    db: Session,
    data: UserOrganizationCreationSchema,
) -> UserOrganization:
    try:
        if data.auth_code and data.password:
            # STANDARD SIGNUP
            user_info: User = get_user_by_auth_code(data.auth_code, db)
        elif not data.auth_code and not data.password:
            # OAUTH2 SIGNUP
            user_info = get_user_by_email(data.email, db)
        else:
            raise ValidationError(messages.INVALID_DB_ARG)
        if not user_info and data.auth_code:
            raise ValidationError(messages.INVALID_CODE)
        if not user_info and not data.auth_code:
            raise ValidationError(messages.EMAIL_NOT_EXISTS)
        organization = Organization(
            company_name=data.company_name,
            domain=data.domain,
            company_size=data.company_size.value,
        )
        user_info.first_name = data.first_name
        user_info.last_name = data.last_name
        user_info.business_phone_number = data.business_phone_number
        user_info.country_id = data.country_or_region
        user_info.active = True
        user_info.auth_code = None
        user_info.password = get_password_hash(data.password) if data.password else None

        user_organization = UserOrganization(
            organization=organization,
            user=user_info,
            user_type=UserTypes.owner,
            verification_status=VerificationStatusTypes.active,
        )
        insert_data(db, user_organization)
        return user_info
    except SQLAlchemyError:
        db.rollback()
        raise ValidationError(messages.INVALID_DB_ARG)


def check_user_in_organization(
    user_id: int, organization_id: int, db: Session
) -> UserOrganization | None:
    return (
        db.query(UserOrganization)
        .filter_by(user_id=user_id, organization_id=organization_id)
        .first()
    )


def insert_user_organization(
    organization_id: int,
    user_id: int,
    verification_status: VerificationStatusTypes,
    verification_code: str,
    db: Session,
):
    user_organization = UserOrganization(
        organization_id=organization_id,
        user_id=user_id,
        verification_status=verification_status,
        verification_code=verification_code,
    )
    return insert_data(db, user_organization)


def refresh_invitation_info(
    user_organization: UserOrganization,
    verification_code: str,
    db: Session,
):
    user_organization.verification_code = verification_code
    user_organization.verification_status = VerificationStatusTypes.pending
    insert_data(db, user_organization)


def check_invitation_code(verification_code: str, db: Session):
    return (
        db.query(UserOrganization)
        .filter_by(
            verification_code=verification_code,
            verification_status=VerificationStatusTypes.pending,
        )
        .first()
    )


def all_user_organization(user_id: int, db: Session):
    return (
        db.query(UserOrganization)
        .filter_by(user_id=user_id, verification_status=VerificationStatusTypes.pending)
        .all()
    )


def refresh_verification_status(
    user_id: int,
    db: Session,
):
    user_organizations_list = all_user_organization(user_id, db)
    for user_organization in user_organizations_list:
        user_organization.verification_status = VerificationStatusTypes.active
        user_organization.verification_code = None
        insert_data(db, user_organization)


def del_user_organization(user_organization: UserOrganization, db: Session):
    user_organization.verification_status = VerificationStatusTypes.deleted
    insert_data(db, user_organization)


def user_organizations(user_id: int, db: Session) -> Union[List[Organization], List]:
    organizations = (
        db.query(Organization)
        .join(UserOrganization, Organization.id == UserOrganization.organization_id)
        .filter(
            UserOrganization.user_id == user_id,
            UserOrganization.verification_status == VerificationStatusTypes.active,
        )
        .all()
    )
    return organizations
