from pydantic import BaseModel

from app.routers.auth.schema import EmailString, UserSchema


class GetOrganizationUsersSchema(BaseModel):
    organization_id: int


class OrganizationUsersSchema(BaseModel):
    users: list[UserSchema]


class TeamInvitationSchema(BaseModel):
    email: EmailString


class AcceptSchema(BaseModel):
    code: str


class OrganizationConfigSchema(BaseModel):
    company_name: str
    id: int
    domain: str


class OrganizationSchema(BaseModel):
    organizations: list[OrganizationConfigSchema]
