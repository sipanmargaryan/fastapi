from datetime import timedelta
from functools import partial
from typing import List

import pydantic
import yaml
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.helpers import messages, vault
from app.helpers.database import get_db
from app.helpers.dbt_runner import update_dbt_configs, update_dbt_models
from app.helpers.download_folder import download_folder_zip
from app.helpers.exceptions import (
    AuthenticationFailedError,
    MeltanoError,
    NotFound,
    ValidationError,
)
from app.helpers.jwt import create_access_token
from app.helpers.mail import send_mail
from app.helpers.middlewares import is_admin_middleware, is_super_user_middleware
from app.helpers.minio import add_file_to_minio, sync_configs_minio_local
from app.helpers.response import Response
from app.routers.admin.crud import (
    company_domain_exists_in_db,
    create_admin,
    get_active_admin_by_email,
    get_organization_owner,
    save_chart_data_in_db,
)
from app.routers.admin.schemas.credentials import (
    ChartConfigSchema,
    DashboardSchema,
    EnvironmentVariableSchema,
)
from app.routers.admin.schemas.dbt_schemas import DBTConfigSchema
from app.routers.admin.schemas.schema import AdminUserSchema
from app.routers.admin.tasks import dbt_run_task, meltano_run_task
from app.routers.admin.utils import (
    create_chart_yaml,
    create_meltano_config,
    data_type_response_model,
)
from app.routers.auth.crud import get_domain
from app.routers.auth.models import AdminTypes
from app.routers.auth.schema import UserLoginSchema, UserTokenPayload
from app.routers.auth.utils import get_token_payload, verify_password
from app.routers.dashboard.crud import (
    check_user_in_dashboard,
    create_dashboard,
    insert_user_dashboard,
)
from app.settings import FRONT_API
from app.worker import celery_app

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={status.HTTP_404_NOT_FOUND: NotFound().to_response(is_json=False)},
)


@router.post("/add-environment-variables")
async def add_variables(
    request: EnvironmentVariableSchema,
    db: Session = Depends(get_db),
    admin_info: UserTokenPayload = Depends(is_admin_middleware()),
):
    company_domain = request.company_domain
    data_source_type = request.data_source_type
    if not company_domain_exists_in_db(company_domain, db):
        raise ValidationError(messages.COMPANY_NOT_FOUND)
    environment_variables = request.environment_variables
    schema = data_type_response_model(data_source_type)
    try:
        data = schema(**environment_variables)
    except pydantic.ValidationError as e:
        errors_info = {
            error["loc"][0]: f"Message: {error['msg']}, Error type: {error['type']}"
            for error in e.errors()
        }
        raise ValidationError(message=errors_info)
    data = jsonable_encoder(data)

    client = vault.SSMParameterStoreClient()
    old_variables = {}
    try:
        old_variables = client.get_parameter(company_domain)
    except ClientError:
        pass
    input_variables = {data_source_type: environment_variables}
    updated_variables = {**old_variables, **input_variables}
    client.set_parameter(company_domain, updated_variables)
    return Response(data=data, message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/sign-in")
async def sign_in(
    user_data: UserLoginSchema,
    is_super_user: bool = Query(False),
    db: Session = Depends(get_db),
):
    if is_super_user:
        user = get_active_admin_by_email(user_data.email, AdminTypes.superuser, db)
    else:
        user = get_active_admin_by_email(user_data.email, AdminTypes.consultant, db)
    if user is None:
        raise AuthenticationFailedError()
    if not verify_password(user_data.password, user.password):
        raise AuthenticationFailedError()
    token_payload = get_token_payload(user)
    data = create_access_token(token_payload, expires_delta=timedelta(days=1))
    return Response(
        data={"access_token": data}, message=messages.SUCCESS, code=status.HTTP_200_OK
    )


@router.post("/update-or-create-dashboard-and-chart")
async def update_or_create_dashboard_and_chart(
    files: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_info: UserTokenPayload = Depends(is_admin_middleware()),
):
    chart_config_file = files.file
    yaml_content = chart_config_file.read().decode("utf-8")
    yaml_data = yaml.safe_load(yaml_content)
    chart_content = yaml_data["dashboards"]
    try:
        chart_content = DashboardSchema(**chart_content)
    except ValidationError as e:
        raise ValidationError()

    domain = chart_content.domain
    add_file_to_minio(domain, files, "configs")
    organization = get_domain(domain, db)
    if organization is None:
        raise ValidationError(messages.COMPANY_NOT_FOUND)
    dashboard_id = create_dashboard(
        chart_content.name,
        organization.id,
        admin_info.user_id,
        chart_content.dashboard_unique_identifier,
        db,
    )
    file_name = files.filename
    create_chart_yaml(yaml_content, domain, file_name)

    chart_data = chart_content.charts
    try:
        chart_data = TypeAdapter(ChartConfigSchema).validate_python(chart_data)
        save_chart_data_in_db(chart_data, dashboard_id, admin_info.user_id, db)
    except ValidationError as e:
        raise ValidationError()

    return Response(message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/dashboard-add-chart")
async def dashboard_add_chart(
    files: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_info: UserTokenPayload = Depends(is_admin_middleware()),
):
    chart_config_file = files.file
    yaml_content = chart_config_file.read().decode("utf-8")
    yaml_data = yaml.safe_load(yaml_content)
    chart_content = yaml_data["dashboards"]
    domain = chart_content["domain"]
    # add_file_to_minio(domain, files, "configs")
    organization = get_domain(domain, db)
    if organization is None:
        raise ValidationError(messages.COMPANY_NOT_FOUND)
    dashboard_id = create_dashboard(
        chart_content["name"],
        organization.id,
        admin_info.user_id,
        chart_content["dashboard_unique_identifier"],
        db,
    )

    organization_owner = get_organization_owner(db, organization.id)
    user_in_dashboard = check_user_in_dashboard(
        organization_owner.user_id, dashboard_id, db
    )
    if not user_in_dashboard:
        insert_user_dashboard(organization_owner.user_id, dashboard_id, db)

    file_name = files.filename
    create_chart_yaml(yaml_content, domain, file_name)

    chart_data = chart_content["charts"]
    try:
        save_chart_data_in_db(chart_data, dashboard_id, admin_info.user_id, db)
    except ValidationError as e:
        raise ValidationError()

    return Response(message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/run-meltano")
async def run_meltano(
    request: Request,
    meltano_config_file: UploadFile = File(...),
    admin_info: UserTokenPayload = Depends(is_admin_middleware()),
):
    yaml_content = meltano_config_file.file.read().decode("utf-8")
    yaml_data = yaml.safe_load(yaml_content)
    meltano_config_data = yaml_data.get("el")
    if not meltano_config_data:
        raise ValidationError

    domain = meltano_config_data["domain"]
    create_meltano_config(yaml_content, meltano_config_file.filename)
    add_file_to_minio(data=meltano_config_file, domain=domain, folder_type="configs")
    meltano_run_task.apply_async(
        kwargs={"yaml_content": meltano_config_data, "domain": domain}
    )

    return Response(message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.post("/run-dbt")
async def run_dbt(
    files: List[UploadFile] = File(...),
    admin_info: UserTokenPayload = Depends(is_admin_middleware()),
):
    dbt_config_file, source_file, *sql_files = files
    yaml_content = dbt_config_file.file.read().decode("utf-8")
    yaml_data = yaml.safe_load(yaml_content)
    dbt_content = yaml_data["dbts"]
    domain = dbt_content["domain"]
    try:
        dbt_content = DBTConfigSchema(**dbt_content)
    except ValidationError:
        raise ValidationError()
    file_name = dbt_config_file.filename
    update_dbt_configs(yaml_content, domain, file_name)
    update_dbt_models(domain, source_file)
    _add_file_to_minio = partial(add_file_to_minio, domain=domain)
    _add_file_to_minio(data=dbt_config_file, folder_type="configs")
    sql_names = ""
    sql_files.append(source_file)
    for file in sql_files:
        update_dbt_models(domain, file)
        _add_file_to_minio(data=file, folder_type="dbts")
        sql_names += " " + file.filename

    task_inspector = celery_app.control.inspect()
    for active_task in task_inspector.active().values():
        for task in active_task:
            if (
                task["name"] == "meltano_run"
                and task["kwargs"]["yaml_content"]["domain"] == domain
            ):
                raise MeltanoError(
                    messages="Meltano extracting and loading processes are running for same domain"
                )

    dbt_run_task.apply_async(kwargs={"domain": domain, "sql_names": sql_names})

    return Response(message=messages.SUCCESS, code=status.HTTP_200_OK)


@router.get("/download-folder/{domain}")
async def download_folder(
    domain: str,
    admin_info: UserTokenPayload = Depends(is_admin_middleware()),
):
    sync_configs_minio_local(domain)
    data = download_folder_zip(domain)
    return StreamingResponse(
        data, media_type="application/zip", status_code=status.HTTP_200_OK
    )


@router.post("/create-admin-user")
async def create_admin_user(
    request: AdminUserSchema,
    super_user: UserTokenPayload = Depends(is_super_user_middleware()),
    db: Session = Depends(get_db),
):
    create_admin(request, db)

    await send_mail(
        messages.EmailSubjects.CONSULTANT_INVITATION,
        request.email,
        dict(
            content="Admin",
            recipient="User User",
            subject="admin",
            reset_pass_link=f"{FRONT_API}",
        ),
        "forgot",
    )
    return Response(message=messages.SUCCESS, code=status.HTTP_200_OK)
