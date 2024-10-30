from typing import Dict, List

from sqlalchemy import delete, insert, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.routers.admin.schemas.credentials import ChartConfigSchema
from app.routers.admin.schemas.schema import AdminUserSchema
from app.routers.auth.crud import insert_data
from app.routers.auth.models import AdminTypes, User
from app.routers.auth.utils import get_password_hash
from app.routers.dashboard.models import Chart
from app.routers.organization.models import Organization, UserOrganization


def company_domain_exists_in_db(domain: str, db: Session) -> Organization | None:
    return db.query(Organization).filter_by(domain=domain).first() is not None


def get_active_admin_by_email(
    email: str, admin_type: AdminTypes, db: Session
) -> User | None:
    return (
        db.query(User)
        .filter_by(email=email, active=True, admin_type=admin_type)
        .first()
    )


def save_chart_data_in_db(
    chart_data: List[Dict], dashboard_id: int, consultant_id: int, db: Session
) -> List[Chart] | None:
    existing_chart_models = (
        db.query(Chart)
        .filter(
            Chart.dashboard_id == dashboard_id, Chart.consultant_id == consultant_id
        )
        .all()
    )

    chart_unique_identifiers = set(
        config["dashboard_chart_unique_identifier"] for config in chart_data
    )

    for chart_model in existing_chart_models:
        if (
            chart_model.dashboard_chart_unique_identifier
            not in chart_unique_identifiers
        ):
            db.delete(chart_model)

    for config in chart_data:
        chart_model = (
            db.query(Chart)
            .filter(
                Chart.dashboard_id == dashboard_id,
                Chart.consultant_id == consultant_id,
                Chart.dashboard_chart_unique_identifier
                == config["dashboard_chart_unique_identifier"],
            )
            .first()
        )

        if chart_model:
            chart_model.config = config
            chart_model.name = config["name"]
        else:
            chart_model = Chart(
                config=config,
                dashboard_id=dashboard_id,
                name=config["name"],
                consultant_id=consultant_id,
                dashboard_chart_unique_identifier=config[
                    "dashboard_chart_unique_identifier"
                ],
            )

            db.add(chart_model)

    db.commit()
    return chart_data


def create_admin(admin_info: AdminUserSchema, db: Session):
    password_hash = get_password_hash(admin_info.password)
    instance = User(
        email=admin_info.email,
        password=password_hash,
        first_name=admin_info.first_name,
        last_name=admin_info.last_name,
        active=True,
        admin_type=AdminTypes.consultant,
    )
    insert_data(db, instance)


def get_organization_owner(db: Session, organization_id: int):
    return (
        db.query(UserOrganization)
        .filter_by(
            organization_id=organization_id,
        )
        .first()
    )
