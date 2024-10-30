from enum import Enum
from typing import Annotated, List, Literal, Union

from pydantic import BaseModel, Field


class AvailableCredentials(str, Enum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    S3 = "s3"
    SNOWFLAKE = "snowflake"


class EnvironmentVariableSchema(BaseModel):
    company_domain: str
    data_source_type: AvailableCredentials
    environment_variables: dict


class PostgresEnvironmentVariableSchema(BaseModel):
    host: str
    port: int
    database: str
    user: str
    password: str


class MySqlEnvironmentVariableSchema(BaseModel):
    host: str
    port: int
    database: str
    user: str
    password: str


class S3EnvironmentVariableSchema(BaseModel):
    access_key: str
    secret_key: str
    bucket_name: str


class SnowflakeEnvironmentVariableSchema(BaseModel):
    account: str
    user: str
    password: str
    role: str
    warehouse: str
    database: str


class ChartType(str, Enum):
    multi_line = "multi_line"
    single_line = "single_line"
    pie_no_center = "pie_no_center"
    pie_with_center = "pie_with_center"
    horizontal_bar = "horizontal_bar"
    vertical_bar = "vertical_bar"
    scatter = "scatter"
    area = "area"
    composed = "composed"
    radar = "radar"
    radar_bar = "radar_bar"


class SingleLineMetricsSchema(BaseModel):
    x_axis: str
    y_axis: str


class ChartSingleLineSchema(BaseModel):
    name: str
    dashboard_chart_unique_identifier: str
    source_table: str
    type: Literal[ChartType.single_line]
    metrics: SingleLineMetricsSchema


class MultiLineMetricsSchema(BaseModel):
    x_axis: str
    y_axis: str
    group_by: str


class ChartMultiLineSchema(BaseModel):
    name: str
    dashboard_chart_unique_identifier: str
    source_table: str
    type: Literal[ChartType.multi_line]
    metrics: MultiLineMetricsSchema


class PieNoCenterMetricsSchema(BaseModel):
    column: str


class ChartPieNoCenterSchema(BaseModel):
    name: str
    dashboard_chart_unique_identifier: str
    sql: str
    type: Literal[ChartType.pie_no_center]
    metrics: PieNoCenterMetricsSchema


class PieWithCenterMetricsSchema(BaseModel):
    column: str


class ChartPieWithCenterSchema(BaseModel):
    name: str
    dashboard_chart_unique_identifier: str
    source_table: str
    type: Literal[ChartType.pie_with_center]
    metrics: PieWithCenterMetricsSchema


class HorizontalBarMetricsSchema(BaseModel):
    x_axis: str
    y_axis: str
    group_by: str


class ChartHorizontalBarSchema(BaseModel):
    name: str
    dashboard_chart_unique_identifier: str
    source_table: str
    type: Literal[ChartType.horizontal_bar]
    metrics: HorizontalBarMetricsSchema


class VerticalBarMetricsSchema(BaseModel):
    x_axis: str
    y_axis: str
    group_by: str


class ChartVerticalBarSchema(BaseModel):
    name: str
    dashboard_chart_unique_identifier: str
    source_table: str
    type: Literal[ChartType.vertical_bar]
    metrics: VerticalBarMetricsSchema


class ScatterMetricsSchema(BaseModel):
    x_axis: str
    y_axis: str
    group_by: str


class ChartScatterSchema(BaseModel):
    name: str
    dashboard_chart_unique_identifier: str
    source_table: str
    type: Literal[ChartType.scatter]
    metrics: ScatterMetricsSchema


ChartConfigSchema = list[
    Annotated[
        Union[
            ChartSingleLineSchema,
            ChartMultiLineSchema,
            ChartPieNoCenterSchema,
            ChartPieWithCenterSchema,
            ChartHorizontalBarSchema,
            ChartVerticalBarSchema,
            ChartScatterSchema,
        ],
        Field(discriminator="type"),
    ]
]


class DashboardSchema(BaseModel):
    name: str
    domain: str
    dashboard_unique_identifier: str
    charts: List
