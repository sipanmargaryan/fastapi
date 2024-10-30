import json

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.helpers import messages
from app.helpers.database import get_db
from app.helpers.exceptions import NotFound, ValidationError
from app.helpers.middlewares import is_member_middleware, is_owner_middleware
from app.helpers.response import Response

from ...helpers.mail import send_mail
from ...settings import FRONT_API
from ..auth.crud import create_user, get_user_by_email
from ..auth.utils import generate_auth_code
from ..organization.crud import (
    check_user_in_organization,
    insert_user_organization,
    refresh_invitation_info,
)
from ..organization.models import VerificationStatusTypes
from .chart_data_creator import CHART_TYPES_SQL, ChartFactory
from .crud import (
    check_user_in_dashboard,
    dashboard_delete,
    del_dashboard_user,
    get_charts_config,
    get_charts_data,
    get_dashboard_members,
    get_dashboards,
    get_domain_by_dashboard_id,
    get_ordered_pinned_dashboard,
    get_shared_dashboards_by_user,
    insert_user_dashboard,
    update_dashboard_last_viewed,
    update_dashboard_name,
    update_dashboard_pin,
)
from .schema import (
    DashboardListSchema,
    DashboardMemberListSchema,
    DashboardPinSchema,
    DashboardRenameSchema,
    ShareDashboardSchema,
    SortBy,
    UserDashboardLastViewSchema,
    UserInfoSchema,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    responses={status.HTTP_404_NOT_FOUND: NotFound().to_response(is_json=False)},
)


@router.get("/dashboards")
async def dashboard(
    search: str = Query(default=""),
    sort_by: SortBy = Query(default=""),
    db: Session = Depends(get_db),
    user: UserInfoSchema = Depends(is_member_middleware()),
):
    dashboard_items = get_dashboards(db, search, sort_by, user)
    dashboards = DashboardListSchema(dashboards=dashboard_items).model_dump()
    return Response(
        data=dashboards["dashboards"], message=messages.SUCCESS, code=status.HTTP_200_OK
    )


@router.patch("/pin")
async def pin_dashboard(
    request: DashboardPinSchema,
    db: Session = Depends(get_db),
    user: UserInfoSchema = Depends(is_member_middleware()),
):
    update_dashboard_pin(user.user_id, request.dashboard_id, db)
    return Response(message=messages.SUCCESS, code=status.HTTP_202_ACCEPTED)


@router.patch("/rename")
async def rename_dashboard(
    request: DashboardRenameSchema,
    db: Session = Depends(get_db),
    user: UserInfoSchema = Depends(is_owner_middleware()),
):
    update_dashboard_name(request.name, request.dashboard_id, db)
    return Response(message=messages.SUCCESS, code=status.HTTP_202_ACCEPTED)


@router.delete("/delete/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    user: UserInfoSchema = Depends(is_owner_middleware()),
):
    dashboard_delete(dashboard_id, db)
    return Response(message=messages.SUCCESS, code=status.HTTP_202_ACCEPTED)


@router.delete("/{dashboard_id}/delete-user/{user_id}")
async def delete_dashboard_user(
    dashboard_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: UserInfoSchema = Depends(is_owner_middleware()),
):
    del_dashboard_user(user_id, dashboard_id, db)
    return Response(message=messages.SUCCESS, status_code=status.HTTP_202_ACCEPTED)


@router.get("/pinned-dashboards")
async def pinned_dashboards(
    db: Session = Depends(get_db),
    user: UserInfoSchema = Depends(is_owner_middleware()),
):
    dashboard_items = get_ordered_pinned_dashboard(user, db)
    dashboards = DashboardListSchema(dashboards=dashboard_items).model_dump()
    return Response(
        data=dashboards["dashboards"], message=messages.SUCCESS, code=status.HTTP_200_OK
    )


@router.get("/get-shared-dashboards/{user_id}")
async def get_shared_dashboards(
    user_id: int,
    user: UserInfoSchema = Depends(is_owner_middleware()),
    db: Session = Depends(get_db),
):
    shared_dashboards = get_shared_dashboards_by_user(user_id, user, db)
    dashboards = DashboardListSchema(dashboards=shared_dashboards).model_dump()
    return Response(
        data=dashboards["dashboards"], message=messages.SUCCESS, code=status.HTTP_200_OK
    )


@router.post("/share-dashboard")
async def share(
    request: ShareDashboardSchema,
    db: Session = Depends(get_db),
    user_info: UserInfoSchema = Depends(is_owner_middleware()),
):
    verification_code = generate_auth_code()
    user = get_user_by_email(request.email, db)
    if user and user.active:
        user_in_organization = check_user_in_organization(
            user.id, user_info.organization_id, db
        )
        if not user_in_organization:
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
            user_info.user_id,
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

    user_dashboard = check_user_in_dashboard(user.id, request.dashboard_id, db)
    if user_dashboard:
        return ValidationError(message=messages.DASHBOARD_MEMBER_ALREADY_EXIST)
    else:
        insert_user_dashboard(user.id, request.dashboard_id, db)

    return Response(message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.get("/{dashboard_id}/chart-data")
async def chart_data(
    dashboard_id: int,
    db: Session = Depends(get_db),
    user: UserInfoSchema = Depends(is_owner_middleware()),
):
    chart_config_data = []
    for chart_config in get_charts_config(dashboard_id, db):
        config = json.loads(chart_config.config)

        chart_config_data.append(config)

    db_name = get_domain_by_dashboard_id(dashboard_id, db)

    chart_types_sql_list = [
        {
            "sql_string": CHART_TYPES_SQL[chart_config["type"]],
            "type": chart_config["type"],
            "metrics": chart_config["metrics"],
            "source_table": chart_config["source_table"],
        }
        for chart_config in chart_config_data
    ]
    chart_data_list = await ChartFactory.create_chart(db_name, chart_types_sql_list)
    update_dashboard_last_viewed(user.user_id, dashboard_id, db)
    return Response(
        data=chart_data_list,
        message=messages.SUCCESS,
        code=status.HTTP_200_OK,
    )


@router.get("/{dashboard_id}/charts")
async def charts(
    dashboard_id: int,
    db: Session = Depends(get_db),
    # user: UserInfoSchema = Depends(is_owner_middleware()),
):
    chart_config_data = []
    for chart_config in get_charts_config(dashboard_id, db):
        config = chart_config.config

        chart_config_data.append(config)

    db_name = get_domain_by_dashboard_id(dashboard_id, db)

    chart_data_list = await get_charts_data(db_name, chart_config_data)

    # update_dashboard_last_viewed(user.user_id, dashboard_id, db)
    return Response(
        data=chart_data_list,
        message=messages.SUCCESS,
        code=status.HTTP_200_OK,
    )


@router.get("/{dashboard_id}/members")
async def dashboard_members_list(
    dashboard_id: int,
    db: Session = Depends(get_db),
    members: DashboardMemberListSchema = Depends(is_member_middleware()),
):
    members_data_list = []
    for member in get_dashboard_members(dashboard_id, db):
        members_data_list.append(
            {
                "user_id": member.user_id,
                "email": member.email,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "image": member.image,
            }
        )

    return Response(
        data=members_data_list,
        message=messages.SUCCESS,
        code=status.HTTP_200_OK,
    )
