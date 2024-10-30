from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

import jwt
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from app.settings import JWT_SECRET

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from .exceptions import JWTExpiredSignatureError, JWTInvalidTokenError, JWTTokenError

SECRET_KEY = JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


def jwt_exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ExpiredSignatureError:
            raise JWTExpiredSignatureError
        except InvalidTokenError:
            raise JWTInvalidTokenError
        except PyJWTError:
            raise JWTTokenError
        except Exception as ex:
            # Exception unrelated to JWT
            raise ex

    return wrapper


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt_encode(to_encode)


def create_refresh_token(data: dict):
    return create_access_token(
        data, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )


@jwt_exception_handler
def jwt_decode(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])


@jwt_exception_handler
def jwt_encode(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm=ALGORITHM)
