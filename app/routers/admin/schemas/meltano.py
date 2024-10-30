from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class SourceTypeEnum(str, Enum):
    tap_s3_csv = "s3"
    tap_postgres = "postgres"
    tap_mysql = "mysql"
    tap_snowflake = "snowflake"


class MeltanoAbstractBaseSchema(BaseModel):
    domain: str


class MeltanoS3TableSchema(BaseModel):
    table_name: str
    key_properties: list[str]
    search_pattern: str | None = Field(default=".*")
    search_prefix: str | None = Field(default="")


class MeltanoS3Schema(MeltanoAbstractBaseSchema):
    source_type: Literal[SourceTypeEnum.tap_s3_csv]
    access_key: str
    secret_key: str
    bucket_name: str
    tables: list[MeltanoS3TableSchema]
    start_date: str = "1970-01-01"


class MeltanoPostgresSchema(MeltanoAbstractBaseSchema):
    source_type: Literal[SourceTypeEnum.tap_postgres]
    host: str
    database: str
    user: str
    password: str
    db_schema: list[str] = [Field(default="public", alias="schema")]
    port: int = 5432


class MeltanoSnowflakeSchema(MeltanoAbstractBaseSchema):
    source_type: Literal[SourceTypeEnum.tap_snowflake]
    account: str
    user: str
    password: str
    warehouse: str


class MeltanoMysqlSchema(MeltanoAbstractBaseSchema):
    source_type: Literal[SourceTypeEnum.tap_mysql]
    host: str
    database: str
    user: str
    password: str
    db_schema: list[str] = [Field(default="public", alias="schema")]
    port: int = 3306


MeltanoVaultConfigSchema = Annotated[
    Union[
        MeltanoS3Schema,
        MeltanoPostgresSchema,
        MeltanoMysqlSchema,
        MeltanoSnowflakeSchema,
    ],
    Field(discriminator="source_type"),
]
