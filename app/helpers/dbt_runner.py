import os
import subprocess

from fastapi import UploadFile

from app.settings import CONFIG_FOLDER, DBT_FOLDER, ORGANIZATION_FILE_PATH


def update_dbt_configs(yaml_data: str, domain: str, file_name: str):
    config_path = os.path.join(ORGANIZATION_FILE_PATH, domain, CONFIG_FOLDER)
    with open(os.path.join(config_path, file_name), "w") as config_file:
        config_file.write(yaml_data)


def update_dbt_models(domain: str, files: UploadFile):
    config_path = os.path.join(ORGANIZATION_FILE_PATH, domain, DBT_FOLDER)
    contents = files.file.read().decode("utf-8")

    with open(os.path.join(config_path, files.filename), "w") as f:
        f.write(contents)


def run_custom_dbt(domain: str, sql_names: str):
    command = f"""
                  dotenv set MODELS_PATH ../../elt/{domain}/dbts;
                  cd meltano_el;
                  meltano config dbt-postgres set dbname {domain};
                  meltano invoke dbt-postgres run --select {sql_names} --target-path ../.meltano/transformers/dbt/target;
                  cd .."""

    try:
        subprocess.call(command, shell=True)
    except Exception as e:
        return e
