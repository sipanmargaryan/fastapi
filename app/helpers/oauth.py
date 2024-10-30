from enum import Enum
from urllib.parse import quote

from httpx import AsyncClient
from oauthlib.oauth2 import WebApplicationClient
from pydantic import BaseModel, Field

from app.helpers.exceptions import AuthenticationFailedError
from app.helpers.messages import INVALID_SOCIAL_AUTH_CODE
from app.settings import (
    FRONT_API,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    REDIRECT_URL,
)


class ProviderEnum(Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class BaseData(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str


class AuthToken(BaseModel):
    access_token: str
    refresh_token: str = Field(default=None)


class GrantTypeAuthCode(BaseData):
    code: str = Field(default=None)
    grant_type: str = Field(default="authorization_code")


class OAuth2Client:
    def __init__(self, client_secret, client_id, **kwargs):
        self.provider = kwargs.get("provider", None)
        self.__oauth2_client = WebApplicationClient(client_id=client_id)
        self.__auth_code_data = GrantTypeAuthCode(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URL,
        )
        self.__token_url = kwargs.get("token_url", None)
        self.__user_info_url = kwargs.get("user_info_url", None)
        self.__client_secret = client_secret
        self.__client_id = client_id

    @property
    def user_info_url(self):
        return self.__user_info_url

    @property
    def token_url(self):
        return self.__token_url

    @property
    def client_secret(self):
        return self.__client_secret

    @property
    def client_id(self):
        return self.__client_id

    async def get_tokens(self, code):
        self.__auth_code_data.code = quote(code, safe="")
        try:
            async with AsyncClient() as client:
                if self.provider == ProviderEnum.MICROSOFT:
                    response = await client.post(
                        self.token_url,
                        data=self.__auth_code_data.model_dump(),
                    )
                else:
                    response = await client.post(
                        self.token_url,
                        params=self.__auth_code_data.model_dump(),
                    )
                return AuthToken.model_validate(response.json())
        except Exception as e:
            raise AuthenticationFailedError(INVALID_SOCIAL_AUTH_CODE)

    async def get_user_info(self, access_token):
        try:
            async with AsyncClient() as client:
                response = await client.get(
                    self.user_info_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                return response.json()
        except Exception as e:
            raise AuthenticationFailedError(INVALID_SOCIAL_AUTH_CODE)


class GoogleAuth(OAuth2Client):
    def __init__(self, client_secret, client_id):
        self.__token_url = "https://oauth2.googleapis.com/token"
        self.__user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        super().__init__(
            client_secret,
            client_id,
            token_url=self.__token_url,
            user_info_url=self.__user_info_url,
            provider=ProviderEnum.GOOGLE,
        )


class MicrosoftAuth(OAuth2Client):
    def __init__(self, client_secret, client_id):
        self.__token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        self.__user_info_url = "https://graph.microsoft.com/v1.0/me"
        super().__init__(
            client_secret,
            client_id,
            token_url=self.__token_url,
            user_info_url=self.__user_info_url,
            provider=ProviderEnum.MICROSOFT,
        )


class OAuthClientFactory:
    @staticmethod
    def create_oauth_client(client_type: ProviderEnum):
        if client_type.value == ProviderEnum.GOOGLE.value:
            return GoogleAuth(
                client_secret=GOOGLE_CLIENT_SECRET,
                client_id=GOOGLE_CLIENT_ID,
            )
        elif client_type.value == ProviderEnum.MICROSOFT.value:
            return MicrosoftAuth(
                client_secret=MICROSOFT_CLIENT_SECRET,
                client_id=MICROSOFT_CLIENT_ID,
            )
        else:
            raise ValueError("Invalid client type")


async def get_user_info_from_provider(provider, code):
    oauth = OAuthClientFactory.create_oauth_client(client_type=provider)
    tokens = await oauth.get_tokens(code)
    user_info = await oauth.get_user_info(tokens.access_token)
    try:
        info = {
            "first_name": user_info["given_name"].strip(),
            "last_name": user_info["family_name"].strip(),
            "email": user_info["email"].strip(),
        }
    except KeyError:
        info = {
            "first_name": user_info["givenName"].strip(),
            "last_name": user_info["surname"].strip(),
            "email": user_info["mail"].strip(),
        }
    return info
