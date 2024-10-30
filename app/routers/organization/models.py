import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, event
from sqlalchemy.dialects.postgresql import ENUM as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.helpers.database import BaseDBModel
from app.routers.auth.models import User


class UserTypes(str, enum.Enum):
    member = "member"
    owner = "owner"


class VerificationStatusTypes(str, enum.Enum):
    pending = "pending"
    active = "active"
    deleted = "deleted"
    expired = "expired"


class Organization(BaseDBModel):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    company_name = Column(String)
    domain = Column(String, unique=True)
    company_size = Column(String)


class UserOrganization(BaseDBModel):
    __tablename__ = "user_organization"

    id = Column(Integer, primary_key=True)
    user_type = Column(SQLAlchemyEnum(UserTypes), default=UserTypes.member)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship(User, backref="user_organizations")
    organization = relationship(Organization, backref="organization_users")
    invitation_date = Column(DateTime, default=datetime.utcnow())

    verification_status = Column(
        SQLAlchemyEnum(VerificationStatusTypes), default=VerificationStatusTypes.pending
    )
    verification_code = Column(String, unique=True)


@event.listens_for(Organization, "before_update")
@event.listens_for(UserOrganization, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
