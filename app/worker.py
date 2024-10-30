from celery import Celery, Task
from celery.schedules import crontab

from app.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery_app = Celery(__name__)
celery_app.autodiscover_tasks(
    ["app.routers.admin.tasks", "app.routers.organization.tasks"]
)
celery_app.conf.broker_url = CELERY_BROKER_URL
celery_app.conf.result_backend = CELERY_RESULT_BACKEND
celery_app.conf.broker_connection_retry_on_startup = True


celery_app.conf.beat_schedule = {
    "mark_invitation_expired": {
        "task": "app.routers.organization.tasks.mark_invitation_expired",
        "schedule": crontab(minute=0, hour="*"),
    },
}

celery_app.conf.timezone = "UTC"


class BaseCeleryTask(Task):
    ignore_result = True

    def on_success(self, retval, task_id, args, kwargs):
        ...

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        ...
