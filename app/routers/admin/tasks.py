from app.helpers.dbt_runner import run_custom_dbt
from app.helpers.meltano_factory import meltano_factory
from app.helpers.minio import sync_configs_minio_local
from app.helpers.slack_insights import send_slack_notification
from app.worker import BaseCeleryTask, celery_app


@celery_app.task(name="meltano_run", base=BaseCeleryTask, retries=2)
def meltano_run_task(domain, yaml_content):
    try:
        sync_configs_minio_local(domain)
        meltano_factory(yaml_content, domain)
        send_slack_notification(
            "EL process has been run successfully for domain: " + domain
        )
    except Exception as e:
        send_slack_notification(
            "Error occurred during Meltano run for domain: " + domain
        )
        raise e


@celery_app.task(name="dbt_run", base=BaseCeleryTask, retries=2)
def dbt_run_task(domain, sql_names):
    try:
        sync_configs_minio_local(domain)
        run_custom_dbt(domain, sql_names)
        send_slack_notification(
            "Transformation has been run successfully for domain: " + domain
        )
    except Exception as e:
        send_slack_notification("Error occurred during DBT run for domain: " + domain)
        raise e
