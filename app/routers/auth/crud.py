from datetime import datetime
from typing import Type

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...helpers import messages
from ...helpers.exceptions import ValidationError
from ..organization.models import (
    Organization,
    UserOrganization,
    VerificationStatusTypes,
)
from .models import Country, User
from .schema import TeamMemberSignUpSchema
from .utils import get_password_hash


def insert_data(db: Session, instance):
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def get_user_by_email(email: str, db: Session) -> User | None:
    return db.query(User).filter_by(email=email).first()


def get_active_user_by_email(email: str, db: Session) -> Type[User] | None:
    return db.query(User).filter_by(email=email, active=True).first()


def get_active_user_by_id(user_id: int, db: Session) -> Type[User] | None:
    return db.query(User).filter_by(id=user_id, active=True).first()


def create_user_by_email(email: str, db: Session) -> User:
    instance = User(email=email)
    insert_data(db, instance)

    return instance


def create_user(db: Session, **kwargs) -> User:
    instance = User(**kwargs)
    insert_data(db, instance)

    return instance


def get_user_by_auth_code(auth_code: str, db: Session) -> Type[User] | None:
    return db.query(User).filter_by(auth_code=auth_code).first()


def update_reset_pass_code(
    user: User, code: str, reset_pass_code_expiration_date: datetime, db: Session
) -> User:
    user.reset_pass_code = code
    user.reset_pass_code_expiration_date = reset_pass_code_expiration_date
    return insert_data(db, user)


def check_user_reset_password_code(code: str, db: Session) -> Type[User] | None:
    current_datetime = datetime.utcnow()
    user = (
        db.query(User)
        .filter(
            User.reset_pass_code == code,
            User.reset_pass_code_expiration_date > current_datetime,
            User.active == True,
        )
        .first()
    )

    return user


def update_auth_code(email: str, code: str, db: Session) -> User:
    user = db.query(User).filter_by(email=email).first()
    if user:
        user.auth_code = code

    return insert_data(db, user)


def update_user_password(
    user: Type[User],
    password: str,
    db: Session,
) -> User:
    from .utils import get_password_hash

    user.password = get_password_hash(password)
    user.reset_pass_code_expiration_date = None
    user.reset_pass_code = None

    return insert_data(db, user)


def get_country(db: Session) -> list[Type[Country]]:
    return db.query(Country).all()


def get_domain(domain, db: Session) -> Organization | None:
    return db.query(Organization).filter_by(domain=domain).first()


def get_user_and_organization_by_domain_name(user_id, domain, db: Session) -> dict:
    user_organization = (
        db.query(
            User.first_name,
            User.last_name,
            User.email,
            User.business_phone_number,
            UserOrganization.user_id,
            UserOrganization.organization_id,
            UserOrganization.user_type,
        )
        .join(UserOrganization, User.id == UserOrganization.user_id)
        .join(Organization, Organization.id == UserOrganization.organization_id)
        .filter(
            User.id == user_id,
            Organization.domain == domain,
            User.active == True,
            UserOrganization.verification_status == VerificationStatusTypes.active,
        )
        .first()
    )
    return user_organization._asdict() if user_organization else None


def get_user_by_id(user_id: int, db: Session) -> Type[User] | None:
    return db.query(User).filter_by(id=user_id).first()


def check_verification_code(
    user_id: int, verification_code: str, verification_status: str, db: Session
) -> UserOrganization | None:
    return (
        db.query(UserOrganization)
        .filter(
            UserOrganization.user_id == user_id,
            UserOrganization.verification_code == verification_code,
            UserOrganization.verification_status == verification_status,
        )
        .first()
    )


def create_team_member(
    db: Session,
    data: TeamMemberSignUpSchema,
    user: User,
    user_organization: UserOrganization,
) -> UserOrganization:
    try:
        user.first_name = data.first_name
        user.last_name = data.last_name
        user.active = True
        user.password = get_password_hash(data.password)

        user_organization.user = user
        user_organization.verification_code = None
        user_organization.verification_status = VerificationStatusTypes.active
        return insert_data(db, user_organization)

    except SQLAlchemyError:
        db.rollback()
        raise ValidationError(messages.INVALID_DB_ARG)
