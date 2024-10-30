import argparse
import random
import string
from datetime import date
from uuid import uuid4

from factory import Faker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyDate

from app.helpers.database import SessionLocal
from app.routers.auth.models import AdminTypes, User
from app.routers.auth.utils import get_password_hash
from app.routers.dashboard.models import Dashboard, UserDashboard
from app.routers.organization.models import (
    Organization,
    UserOrganization,
    UserTypes,
    VerificationStatusTypes,
)

session = SessionLocal()
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-u", "--user", type=str)
arg_parser.add_argument("-o", "--organization", type=str)
arg_parser.add_argument("-c", "--consultant", type=str)

args = arg_parser.parse_args()


class OrganizationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Organization
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    company_name = Faker("company")
    domain = "".join(random.choice(string.ascii_lowercase) for i in range(4))
    company_size = "1 to 5"


class UserConsultantFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    email = Faker("email")
    first_name = "admin"
    last_name = "admin"
    business_phone_number = Faker("phone_number")
    active = True
    admin_type = AdminTypes.consultant
    country_id = 1


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    email = Faker("email")
    password = None
    first_name = "test"
    last_name = "test"
    business_phone_number = Faker("phone_number")
    active = True
    admin_type = None
    country_id = 1


class UserOrganizationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UserOrganization
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    organization_id = None
    user_id = None
    user_type = UserTypes.owner
    verification_status = VerificationStatusTypes.active


class DashboardFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Dashboard
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    name = f"Dashboard-{random.randint(1, 100)}"
    organization_id = None
    consultant_id = None
    dashboard_unique_identifier = str(uuid4())
    created_at = Faker("date_object")


class UserDashboardFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UserDashboard
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    dashboard_id = SubFactory(DashboardFactory)
    user_id = SubFactory(UserFactory)
    last_viewed = FuzzyDate(
        date(2021, 1, 1),
        date(2023, 12, 20),
    )


if __name__ == "__main__":
    args = arg_parser.parse_args()
    _password = get_password_hash("Aa123123#")
    if args.consultant:
        consultant = UserConsultantFactory.build(id=args.consultant)
    else:
        consultant = UserConsultantFactory.create()
    if args.user:
        user = UserFactory.build(id=args.user, password=_password)
    else:
        user = UserFactory.create(password=_password)
    if args.organization:
        organization = OrganizationFactory.build(id=args.organization)
    else:
        organization = OrganizationFactory.create()
        user_organization = UserOrganizationFactory(
            organization_id=organization.id,
            user_id=user.id,
        )
    for _ in range(10):
        dashboard = DashboardFactory.create(
            name=f"Dashboard-{random.randint(1, 100000)}",
            organization_id=organization.id,
            consultant_id=consultant.id,
            dashboard_unique_identifier=str(uuid4()),
        )
        UserDashboardFactory.create(
            user_id=user.id,
            dashboard_id=dashboard.id,
        )
