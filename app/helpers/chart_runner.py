import os

from app.settings import CONFIG_FOLDER, ORGANIZATION_FILE_PATH


def create_chart_yaml(yaml_data: str, domain: str, file_name: str):
    config_path = os.path.join(ORGANIZATION_FILE_PATH, domain, CONFIG_FOLDER)
    with open(os.path.join(config_path, file_name), "wb") as config_file:
        config_file.write(yaml_data.encode("utf-8"))
