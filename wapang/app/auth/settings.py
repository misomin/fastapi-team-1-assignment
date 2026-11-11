from pydantic_settings import BaseSettings, SettingsConfigDict
from wapang.settings import SETTINGS

class AuthSettings(BaseSettings):
    ACCESS_TOKEN_SECRET: str
    REFRESH_TOKEN_SECRET: str
    SHORT_SESSION_LIFESPAN: int = 15
    LONG_SESSION_LIFESPAN: int = 24 * 60

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=SETTINGS.env_file,
        extra='ignore'
    )

AUTH_SETTINGS = AuthSettings()