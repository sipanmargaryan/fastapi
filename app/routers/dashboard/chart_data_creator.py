from app.routers.admin.schemas.credentials import ChartType
from app.routers.dashboard.crud import get_charts_from_db

CHART_TYPES_SQL = {
    ChartType.pie_with_center: """select tbl.{column}, count(*) as percent from {source_table} tbl group by {column};""",
    ChartType.pie_no_center: """select tbl.{column}, count(*) as percent from {source_table} tbl group by {column};""",
    ChartType.single_line: """SELECT {column} FROM {source_table} as tbl;""",
    ChartType.multi_line: """SELECT {column} FROM {source_table} as tbl;""",
    ChartType.horizontal_bar: """SELECT {column} FROM {source_table} as tbl;""",
    ChartType.vertical_bar: """SELECT {column} FROM {source_table} as tbl;""",
    ChartType.scatter: """SELECT {column} FROM {source_table} as tbl;""",
}


#     values default will be all      source_table.filered_column.unique
#         ChartType.scatter: """SELECT {column} FROM {source_table} as tbl WHERE {filered_column} in [values];""",
class ChartFactory:
    @staticmethod
    async def create_chart(db_name, chart_type_list):
        return await get_charts_from_db(db_name, chart_type_list)
