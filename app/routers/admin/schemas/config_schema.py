from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.routers.admin.schemas.credentials import AvailableCredentials


class MeltanoAbstractBaseSchema(BaseModel):
    domain: str


class MeltanoS3TableSchema(BaseModel):
    table_name: str
    key_properties: list[str]
    search_pattern: str | None = Field(default=".*")
    search_prefix: str | None = Field(default="")


class MeltanoAbtsractBaseSchema(BaseModel):
    domain: str


class MeltanoS3Schema(MeltanoAbtsractBaseSchema):
    source_type: Literal[AvailableCredentials.S3]
    tables: list[MeltanoS3TableSchema]
    start_date: str = "1970-01-01"


class MeltanoPostgresSchema(MeltanoAbtsractBaseSchema):
    source_type: Literal[AvailableCredentials.POSTGRES]


class MeltanoMysqlSchema(MeltanoAbtsractBaseSchema):
    source_type: Literal[AvailableCredentials.MYSQL]


class MeltanoSnowflakeSchema(MeltanoAbtsractBaseSchema):
    source_type: Literal[AvailableCredentials.SNOWFLAKE]


MeltanoConfigSchema = Annotated[
    Union[
        MeltanoS3Schema,
        MeltanoPostgresSchema,
        MeltanoMysqlSchema,
        MeltanoSnowflakeSchema,
    ],
    Field(discriminator="source_type"),
]
