import io
import os
from zipfile import ZipFile

from app.helpers import messages
from app.helpers.exceptions import ValidationError
from app.settings import ORGANIZATION_FILE_PATH


def add_folder_to_zip(zip_file, folder_path, parent_folder=""):
    for folder_item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, folder_item)
        if os.path.isdir(item_path):
            add_folder_to_zip(
                zip_file, item_path, os.path.join(parent_folder, folder_item)
            )
        else:
            zip_file.write(item_path, os.path.join(parent_folder, folder_item))


def download_folder_zip(folder_name: str):
    folder_path = os.path.join(ORGANIZATION_FILE_PATH, folder_name)
    if not os.path.isdir(folder_path):
        raise ValidationError(messages.INVALID_DOMAIN)
    zip_buffer = io.BytesIO()
    try:
        with ZipFile(zip_buffer, "w") as zip_file:
            add_folder_to_zip(zip_file, folder_path)
    except Exception:
        raise ValidationError()
    zip_buffer.seek(0)
    return iter([zip_buffer.getvalue()])
