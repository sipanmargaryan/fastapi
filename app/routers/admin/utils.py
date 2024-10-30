import os
from typing import Dict, List, Union

import yaml
from pydantic import TypeAdapter
from pydantic_core._pydantic_core import ValidationError

from app.helpers.exceptions import ValidationError as MeltanoValidationError
from app.routers.admin.schemas.config_schema import MeltanoConfigSchema
from app.routers.admin.schemas.credentials import (
    AvailableCredentials,
    ChartMultiLineSchema,
    ChartSingleLineSchema,
    ChartType,
    MySqlEnvironmentVariableSchema,
    PostgresEnvironmentVariableSchema,
    S3EnvironmentVariableSchema,
    SnowflakeEnvironmentVariableSchema,
)
from app.routers.admin.schemas.meltano import SourceTypeEnum
from app.settings import CONFIG_FOLDER, DBT_FOLDER, ORGANIZATION_FILE_PATH


def data_type_response_model(data_source_type):
    sources = {
        AvailableCredentials.POSTGRES.value: PostgresEnvironmentVariableSchema,
        AvailableCredentials.MYSQL.value: MySqlEnvironmentVariableSchema,
        AvailableCredentials.SNOWFLAKE.value: SnowflakeEnvironmentVariableSchema,
        AvailableCredentials.S3.value: S3EnvironmentVariableSchema,
    }

    return sources.get(data_source_type.value)


def chart_type_response_model(chart_type):
    sources = {
        ChartType.single_line.value: ChartSingleLineSchema,
        ChartType.multi_line.value: ChartMultiLineSchema,
    }

    return sources.get(chart_type.value)


def read_yaml_file(file_path: str) -> Dict[str, Union[str, dict, list]]:
    with open(file_path, "r") as file:
        insights_yaml_config = yaml.safe_load(file)
    return insights_yaml_config


def read_multiple_yaml_configs(
    file_path: str,
) -> List[Dict[str, Union[str, dict, list]]]:
    with open(file_path, "r") as file:
        insights_yaml_configs = yaml.safe_load_all(file)
    return insights_yaml_configs


def create_organization_config_filesystem(domain: str):
    organization_path = os.path.join(ORGANIZATION_FILE_PATH, domain)
    if not os.path.exists(organization_path):
        os.makedirs(organization_path)

    config_folders = [CONFIG_FOLDER, DBT_FOLDER]
    for config in config_folders:
        config_path = os.path.join(organization_path, config)
        os.makedirs(config_path, exist_ok=True)


def serializer_exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            formatted_errors = customize_errors(e.errors())
            raise MeltanoValidationError(formatted_errors) from e

    return wrapper


def customize_errors(errors):
    formatted_errors = ""
    field = "source_type"
    sign = "" if len(errors) == 1 else "\n"
    for error in errors:
        message = error["msg"]
        if error["type"] == "union_tag_invalid":
            message = f'The value should be one of followings {", ".join([item.value for item in SourceTypeEnum])}'
        else:
            field = error["loc"][-1]
        formatted_errors += f"{sign} {field}: {message}"
    return formatted_errors


@serializer_exception_handler
def create_meltano_config(yaml_data: str, file_name: str):
    meltano_config_data = yaml.safe_load(yaml_data)
    if not meltano_config_data:
        raise ValueError("Invalid yaml file")
    meltano_data = TypeAdapter(MeltanoConfigSchema).validate_python(
        meltano_config_data["el"]
    )
    domain = meltano_data.domain
    create_organization_config_filesystem(domain)
    config_path = os.path.join(ORGANIZATION_FILE_PATH, domain, CONFIG_FOLDER)
    with open(os.path.join(config_path, file_name), "w") as meltano_file:
        meltano_file.write(yaml_data)


def create_chart_yaml(yaml_data: str, domain: str, file_name: str):
    config_path = os.path.join(ORGANIZATION_FILE_PATH, domain, CONFIG_FOLDER)
    with open(os.path.join(config_path, file_name), "wb") as config_file:
        config_file.write(yaml_data.encode("utf-8"))
