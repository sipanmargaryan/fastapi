from abc import ABC, abstractmethod

from app.routers.admin.schemas.credentials import ChartType


class ChartDataGenerator(ABC):
    @abstractmethod
    def generate_data(self, chart_config, data):
        pass


class PieChartGenerator(ChartDataGenerator):
    def generate_data(self, chart_config, data):
        label_field = chart_config["label_field"]
        values = []
        for query_result in data:
            data = query_result._asdict()
            values.append(
                {
                    "name": str(data[label_field]),
                    "value": str(data[chart_config["metrics"]["column"]]),
                }
            )

        return {
            "size": 1,
            "type": chart_config["type"],
            "data": values,
            "metrics": chart_config["metrics"],
        }


class LineChartGenerator(ChartDataGenerator):
    def generate_data(self, chart_config, data):
        values = []
        for query_result in data:
            data = query_result._asdict()
            values.append(
                {
                    "name": str(data[chart_config["metrics"]["x-axis"]]),
                    "value": str(data[chart_config["metrics"]["y-axis"]]),
                }
            )

        return {
            "size": 1,
            "type": chart_config["type"],
            "data": values,
            "metrics": chart_config["metrics"],
        }


class BarChartGenerator(ChartDataGenerator):
    def generate_data(self, chart_config, data):
        values = []
        for query_result in data:
            data = query_result._asdict()
            values.append(
                {
                    "name": str(data[chart_config["metrics"]["x-axis"]]),
                    "value": str(data[chart_config["metrics"]["y-axis"]]),
                }
            )

        return {
            "size": 1,
            "type": chart_config["type"],
            "data": values,
            "metrics": chart_config["metrics"],
        }


class MultiLineChartGenerator(ChartDataGenerator):
    def generate_data(self, chart_config, data):
        values = {}
        min_queryset = data[0]
        for queryset in data:
            if len(queryset) < len(min_queryset):
                min_queryset = queryset

        for line_index, queryset in enumerate(data):
            for index, _ in enumerate(min_queryset):
                single_node = queryset[index]._asdict()
                line_name = chart_config["lines"][line_index]["name"]
                name = str(single_node[chart_config["metrics"]["x-axis"]])
                if name in values:
                    values[name].update(
                        {line_name: str(single_node[chart_config["metrics"]["y-axis"]])}
                    )
                else:
                    values[name] = {
                        "name": name,
                        line_name: str(single_node[chart_config["metrics"]["y-axis"]]),
                    }

        return {
            "size": 1,
            "type": chart_config["type"],
            "data": list(values.values()),
            "metrics": chart_config["metrics"],
        }


class ChartGeneratorFactory:
    CHART_GENERATOR = {
        ChartType.pie_no_center: PieChartGenerator(),
        ChartType.single_line: LineChartGenerator(),
        ChartType.vertical_bar: BarChartGenerator(),
        ChartType.horizontal_bar: BarChartGenerator(),
        ChartType.multi_line: MultiLineChartGenerator(),
        ChartType.area: MultiLineChartGenerator(),
        ChartType.composed: MultiLineChartGenerator(),
        ChartType.radar: MultiLineChartGenerator(),
        ChartType.radar_bar: MultiLineChartGenerator(),
    }

    @staticmethod
    def get_chart_data(chart_type):
        return ChartGeneratorFactory.CHART_GENERATOR.get(chart_type)
