import os

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "dev")

# Database
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Auth
JWT_SECRET = os.getenv("JWT_SECRET")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
REDIRECT_URL = os.getenv("REDIRECT_URL")


# Email
class EmailEnv:
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_STARTTLS = False if ENV == "local" else True
    MAIL_SSL_TLS = False
    USE_CREDENTIAL = False if ENV == "local" else True


# Front End
FRONT_API = os.getenv("FRONT_API")

# AWS SSM
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

# Configs
ORGANIZATION_FILE_PATH = os.path.join("elt")
CONFIG_FOLDER = "configs"
DBT_FOLDER = "dbts"

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_BROKER_URL")

# Minio
MINIO_HOST = f"http://{os.getenv('MINIO_HOST')}:{os.getenv('MINIO_PORT')}"
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

# Slack
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL_NAME = "#test"
