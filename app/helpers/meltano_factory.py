import json
import subprocess
from typing import Callable, Final, Union

from pydantic import TypeAdapter

from app.helpers.exceptions import MeltanoError, ValidationError
from app.helpers.vault import SSMParameterStoreClient
from app.routers.admin.schemas.meltano import (
    MeltanoMysqlSchema,
    MeltanoPostgresSchema,
    MeltanoS3Schema,
    MeltanoSnowflakeSchema,
    MeltanoVaultConfigSchema,
    SourceTypeEnum,
)
from app.routers.admin.utils import serializer_exception_handler


class MeltanoExtractor:
    command = None

    @staticmethod
    def set_meltano_configs(*args, **kwargs):
        pass

    @staticmethod
    def run_extractor():
        try:
            subprocess.check_call(
                f"""cd meltano_el && {MeltanoExtractor.command}""", shell=True
            )
        except Exception as e:
            raise MeltanoError() from e


class TapS3Csv(MeltanoExtractor):
    @staticmethod
    def set_meltano_configs(configs: MeltanoS3Schema):
        tables = json.dumps([dict(configs.tables[0])])
        MeltanoExtractor.command = f"""
         meltano config tap-s3-csv set aws_access_key_id {configs.access_key};
         meltano config tap-s3-csv set aws_secret_access_key {configs.secret_key};
         meltano config tap-s3-csv set start_date {configs.start_date};
         meltano config tap-s3-csv set bucket {configs.bucket_name};
         meltano config tap-s3-csv set tables '{tables}';
         meltano config target-postgres set database {configs.domain};
         meltano elt tap-s3-csv target-postgres
        """


class TapPostgres(MeltanoExtractor):
    @staticmethod
    def set_meltano_configs(configs: MeltanoPostgresSchema):
        filter_schemas = json.dumps([i.default for i in configs.db_schema])
        MeltanoExtractor.command = f"""
        meltano config tap-postgres set user {configs.user};
        meltano config tap-postgres set host {configs.host};
        meltano config tap-postgres set port {configs.port};
        meltano config tap-postgres set password {configs.password};
        meltano config tap-postgres set filter_schemas '{filter_schemas}';
        meltano config tap-postgres set database {configs.database};
        meltano config target-postgres set database {configs.domain};
        meltano elt tap-postgres target-postgres
        """


class TapSnowflake(MeltanoExtractor):
    @staticmethod
    def set_meltano_configs(configs: MeltanoSnowflakeSchema):
        MeltanoExtractor.command = f"""
        meltano config tap-snowflake set account {configs.account};
        meltano config tap-snowflake set user {configs.user};
        meltano config tap-snowflake set password {configs.password};
        meltano config tap-snowflake set warehouse {configs.warehouse};
        meltano config target-postgres set database {configs.domain};
        meltano elt tap-snowflake target-postgres
        """


class TapMysql(MeltanoExtractor):
    @staticmethod
    def set_meltano_configs(configs: MeltanoMysqlSchema):
        filter_schemas = json.dumps([i.default for i in configs.db_schema])
        MeltanoExtractor.command = f"""
        meltano config tap-mysql set user {configs.user};
        meltano config tap-mysql set host {configs.host};
        meltano config tap-mysql set port {configs.port};
        meltano config tap-mysql set password {configs.password};
        meltano config tap-mysql set database {configs.database};
        meltano config tap-mysql set filter_schemas '{filter_schemas}';
        meltano config target-mysql set database {configs.domain};
        meltano elt tap-mysql target-mysql
        """


Available_Sources_Annotation = Union[
    TapS3Csv, TapPostgres, TapSnowflake, TapMysql, Callable
]
Available_Schemas_Annotation = Union[
    MeltanoS3Schema,
    MeltanoPostgresSchema,
    MeltanoSnowflakeSchema,
    MeltanoMysqlSchema,
    Callable,
]

SOURCE_TYPES: Final = {
    SourceTypeEnum.tap_s3_csv.value: TapS3Csv,
    SourceTypeEnum.tap_postgres.value: TapPostgres,
    SourceTypeEnum.tap_snowflake.value: TapSnowflake,
    SourceTypeEnum.tap_mysql.value: TapMysql,
}


@serializer_exception_handler
def get_source_credentials(meltano_config_data: dict, domain: str):
    ssm_client = SSMParameterStoreClient()
    ssm_meltano_data = ssm_client.get_parameter(domain)
    ssm_meltano_data = ssm_meltano_data.get(meltano_config_data["source_type"])
    if not ssm_meltano_data:
        raise ValidationError("Please check credentials for the source")
    meltano_config_data.update(ssm_meltano_data)
    return TypeAdapter(MeltanoVaultConfigSchema).validate_python(meltano_config_data)


def meltano_factory(meltano_config_data, domain):
    source_credentials: Available_Schemas_Annotation = get_source_credentials(
        meltano_config_data, domain
    )
    tap_runner_class: Available_Sources_Annotation = SOURCE_TYPES.get(
        source_credentials.source_type
    )
    tap_runner_class.set_meltano_configs(source_credentials)
    tap_runner_class.run_extractor()
