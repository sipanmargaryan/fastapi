from datetime import datetime
from typing import List, Type, Union

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.helpers.chart_data_factory import ChartGeneratorFactory

from ...settings import DB_HOST, DB_PASSWORD, DB_PORT, DB_USER
from ..admin.schemas.credentials import ChartType
from ..organization.models import Organization
from .models import Chart, Dashboard, UserDashboard
from .schema import SortBy, UserInfoSchema


def get_dashboard_by_name(name, db: Session):
    return db.query(Dashboard).filter(Dashboard.name == name).first()


def create_dict_from_db_object_list(db_object_list):
    return [db_object_tuple._asdict() for db_object_tuple in db_object_list]


def get_dashboards(
    db: Session, search: str, sort_by: SortBy, user: UserInfoSchema
) -> Union[List[Dashboard], List]:
    query = (
        db.query(Dashboard.name, Dashboard.id, UserDashboard.pinned)
        .join(UserDashboard, UserDashboard.dashboard_id == Dashboard.id)
        .filter(
            Dashboard.deleted == False,
            UserDashboard.user_id == user.user_id,
            Dashboard.organization_id == user.organization_id,
        )
    )

    if search:
        query = query.filter(Dashboard.name.ilike(f"%{search}%"))

    match sort_by:
        case SortBy.name.value:
            query = query.order_by(Dashboard.name)
        case SortBy.oldest.value:
            query = query.order_by(Dashboard.created_at)
        case SortBy.newest.value:
            query = query.order_by(Dashboard.created_at.desc())
        case SortBy.last_viewed.value:
            query = query.order_by(UserDashboard.last_viewed.desc())
    dashboards = query.all()
    return create_dict_from_db_object_list(dashboards)  # issue with pinned parameter


def insert_data(db: Session, instance):
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def get_dashboard(db: Session) -> Union[List[Dashboard], List]:
    return db.query(Dashboard).all()


def update_dashboard_pin(user_id: int, dashboard_id: int, db: Session) -> Dashboard:
    dashboard = (
        db.query(UserDashboard)
        .filter_by(user_id=user_id, dashboard_id=dashboard_id)
        .first()
    )
    if dashboard:
        if dashboard.pinned:
            dashboard.pinned = False
        else:
            dashboard.pinned = True
        return insert_data(db, dashboard)


def get_dashboard_by_id(dashboard_id: int, db: Session) -> Dashboard:
    return db.query(Dashboard).filter_by(id=dashboard_id).first()


def update_dashboard_name(name: str, dashboard_id: int, db: Session) -> Dashboard:
    dashboard = get_dashboard_by_id(dashboard_id, db)
    if dashboard:
        dashboard.name = name
        return insert_data(db, dashboard)


def dashboard_delete(dashboard_id: int, db: Session) -> None:
    dashboard = get_dashboard_by_id(dashboard_id, db)
    if dashboard:
        dashboard.deleted = True
        return insert_data(db, dashboard)


def del_dashboard_user(user_id: int, dashboard_id: int, db: Session):
    item = (
        db.query(UserDashboard)
        .filter_by(user_id=user_id, dashboard_id=dashboard_id)
        .first()
    )
    db.delete(item)
    db.commit()


def check_user_in_dashboard(
    user_id: int, dashboard_id: int, db: Session
) -> Type[UserDashboard] | None:
    return (
        db.query(UserDashboard)
        .filter_by(user_id=user_id, dashboard_id=dashboard_id)
        .first()
    )


def insert_user_dashboard(
    user_id: int,
    dashboard_id: int,
    db: Session,
):
    user_dashboard = UserDashboard(
        user_id=user_id,
        dashboard_id=dashboard_id,
    )
    return insert_data(db, user_dashboard)


def update_dashboard_last_viewed(
    user_id: int, dashboard_id: int, db: Session
) -> UserDashboard:
    update_query = (
        db.query(UserDashboard)
        .filter(
            UserDashboard.user_id == user_id, UserDashboard.dashboard_id == dashboard_id
        )
        .update({"last_viewed": datetime.utcnow()})
    )
    db.commit()
    return update_query


def get_ordered_pinned_dashboard(
    user: UserInfoSchema, db: Session
) -> Union[List[Dashboard], List]:
    dashboards = (
        db.query(Dashboard.name, Dashboard.id, UserDashboard.pinned)
        .join(UserDashboard, UserDashboard.dashboard_id == Dashboard.id)
        .filter(
            Dashboard.deleted == False,
            UserDashboard.user_id == user.user_id,
            Dashboard.organization_id == user.organization_id,
            UserDashboard.pinned == True,
        )
        .order_by(UserDashboard.pinned_date.desc())
        .all()
    )

    return create_dict_from_db_object_list(dashboards)


def get_shared_dashboards_by_user(
    user_id: int, user: UserInfoSchema, db: Session
) -> Union[List[Dashboard], List]:
    dashboards = (
        db.query(Dashboard.id, Dashboard.name, UserDashboard.pinned)
        .join(UserDashboard, UserDashboard.dashboard_id == Dashboard.id)
        .filter(
            Dashboard.deleted == False,
            UserDashboard.user_id == user_id,
            Dashboard.organization_id == user.organization_id,
        )
        .all()
    )

    return create_dict_from_db_object_list(dashboards)


def create_dashboard(
    name: str,
    organization_id: int,
    consultant_id: int,
    dashboard_unique_identifier: str,
    db: Session,
) -> Dashboard | None:
    _insert = insert(Dashboard).values(
        name=name,
        organization_id=organization_id,
        consultant_id=consultant_id,
        dashboard_unique_identifier=dashboard_unique_identifier,
    )
    _query = _insert.on_conflict_do_update(
        index_elements=["dashboard_unique_identifier"],
        set_={
            "name": name,
        },
    ).returning(Dashboard.id)
    dashboard_id = db.execute(_query).scalar()
    db.commit()
    return dashboard_id


def get_charts_config(dashboard_id: int, db: Session):
    return db.query(Chart).filter_by(dashboard_id=dashboard_id).all()


def get_domain_by_dashboard_id(dashboard_id: int, db: Session):
    return (
        db.query(Organization).join(Dashboard).filter_by(id=dashboard_id).first().domain
    )


def multi_column_chart(**kwargs):
    columns = ",".join(
        [
            '"{chart_config}"'.format(chart_config=chart_config.lower())
            for chart_config in kwargs.values()
        ]
    )
    return columns


def single_column_chart(**kwargs):
    column = list(kwargs.values())[0].lower()
    return f'"{column}"'


def column_tuple_creator(sql_type: ChartType, **kwargs):
    match sql_type:
        case ChartType.single_line:
            return multi_column_chart(**kwargs)
        case ChartType.multi_line:
            return multi_column_chart(**kwargs)
        case ChartType.pie_no_center:
            return single_column_chart(**kwargs)
        case ChartType.pie_with_center:
            return single_column_chart(**kwargs)
        case ChartType.horizontal_bar:
            return multi_column_chart(**kwargs)
        case ChartType.vertical_bar:
            return multi_column_chart(**kwargs)
        case ChartType.scatter:
            return multi_column_chart(**kwargs)


async def get_charts_from_db(db_name, sql_list_chart_config):
    DATABASE_URL = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
    )
    engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=0)
    sql_query_list = []
    async with engine.connect() as connection:
        for chart_config in sql_list_chart_config:
            column = column_tuple_creator(
                chart_config["type"], **chart_config["metrics"]
            )
            sql_query = text(
                chart_config["sql_string"].format(
                    column=column, source_table=chart_config["source_table"]
                )
            )
            result = await connection.execute(sql_query)
            result = result.fetchall()
            sql_query_list.append(
                {
                    "type": chart_config["type"],
                    "data": [query_result._asdict() for query_result in result],
                }
            )
    return sql_query_list


async def get_charts_data(db_name, sql_list_chart_config):
    DATABASE_URL = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
    )
    engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=0)
    sql_query_list = []
    async with engine.connect() as connection:
        for chart_config in sql_list_chart_config:
            if chart_config["type"] in[ChartType.multi_line.value,
                                       ChartType.radar.value,
                                       ChartType.radar_bar.value,
                                       ChartType.composed.value,
                                       ChartType.area.value,
                                    ]:
                result = []
                for line in chart_config["lines"]:
                    sql_query = text(line["sql"])
                    line_data = await connection.execute(sql_query)
                    line_data = line_data.fetchall()
                    result.append(line_data)
            else:
                sql_query = text(chart_config["sql"])
                result = await connection.execute(sql_query)
                result = result.fetchall()

            generator = ChartGeneratorFactory.get_chart_data(chart_config["type"])
            data = generator.generate_data(chart_config, result)
            sql_query_list.append(data)
    return sql_query_list


def get_dashboard_members(dashboard_id: int, db: Session):
    return db.query(UserDashboard).filter_by(dashboard_id=dashboard_id).all()
