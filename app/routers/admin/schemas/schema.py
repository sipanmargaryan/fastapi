from pydantic import BaseModel

from app.routers.auth.schema import EmailString, PasswordString


class AdminUserSchema(BaseModel):
    email: EmailString
    password: PasswordString
    first_name: str
    last_name: str
