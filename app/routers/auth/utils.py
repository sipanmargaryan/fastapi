import random
import re
import secrets
import string
import time
from datetime import datetime, timedelta

from passlib.context import CryptContext

from app.helpers.jwt import create_access_token, create_refresh_token
from app.routers.auth.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def is_valid_password(password: str) -> bool:
    pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{}]).{8,}$"  # issue with password check
    return re.match(pattern, password) is not None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_auth_code() -> str:
    random_string = secrets.token_urlsafe(16)
    timestamp = int(time.time())

    return f"{random_string}-{timestamp}"


def generate_reset_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def get_timedelta_from_hours(**kwargs) -> datetime:
    return datetime.utcnow() + timedelta(**kwargs)


def get_token_payload(data: User) -> dict:
    return {
        "email": data.email,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "user_id": data.id,
        "admin_type": data.admin_type,
    }


def generate_tokens(data: User, refresh: str = "") -> dict:
    tokens = dict(refresh_token=refresh)
    token_payload = get_token_payload(data)
    tokens["access_token"] = create_access_token(token_payload)
    if not refresh:
        tokens["refresh_token"] = create_refresh_token(token_payload)
    return tokens


def is_valid_subdomain(domain: str) -> bool:
    pattern = r"^[a-z0-9][-a-z0-9]*$"
    return re.match(pattern, domain) is not None
