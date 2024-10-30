from boto3 import client

from app.helpers.exceptions import RequestError
from app.routers.admin.utils import create_organization_config_filesystem
from app.settings import (
    MINIO_ACCESS_KEY,
    MINIO_HOST,
    MINIO_SECRET_KEY,
    ORGANIZATION_FILE_PATH,
)

minio_client = client(
    "s3",
    endpoint_url=MINIO_HOST,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)


def add_file_to_minio(domain, data, folder_type):
    bucket_name = ORGANIZATION_FILE_PATH
    file_name = f"{domain}/{folder_type}/{data.filename}"
    data.file.seek(0)
    minio_client.upload_fileobj(data.file, bucket_name, file_name)


def sync_configs_minio_local(domain):
    bucket_name = ORGANIZATION_FILE_PATH
    available_files = minio_client.list_objects(Bucket=bucket_name, Prefix=f"{domain}/")
    if not available_files["Contents"]:
        raise RequestError
    create_organization_config_filesystem(domain)
    for files in available_files["Contents"]:
        file = (
            minio_client.get_object(Bucket=bucket_name, Key=files["Key"])["Body"]
            .read()
            .decode("utf-8")
        )
        with open(f'{ORGANIZATION_FILE_PATH}/{files["Key"]}', "w") as f:
            f.write(file)
