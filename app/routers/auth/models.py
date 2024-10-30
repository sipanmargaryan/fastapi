import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, event
from sqlalchemy.dialects.postgresql import ENUM as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.helpers.database import BaseDBModel


class AdminTypes(str, enum.Enum):
    consultant = "consultant"
    superuser = "superuser"


class User(BaseDBModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    business_phone_number = Column(String)  # issue with unique constraint
    reset_pass_code = Column(String, unique=True)
    auth_code = Column(String, unique=True)
    active = Column(Boolean, default=False)
    reset_pass_code_expiration_date = Column(DateTime, default=None)
    admin_type = Column(SQLAlchemyEnum(AdminTypes), default=None)
    country_id = Column(Integer, ForeignKey("countries.id"))
    country = relationship("Country", backref="users")


class Country(BaseDBModel):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    dial_code = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)


@event.listens_for(User, "before_update")
@event.listens_for(Country, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
