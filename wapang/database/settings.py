from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL
from wapang.settings import SETTINGS


class DatabaseSettings(BaseSettings):
    dialect: str
    driver: str
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def url(self) -> str:
        return URL.create(
            drivername=f"{self.dialect}+{self.driver}",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        ).render_as_string(hide_password=False)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="DB_",
        env_file=SETTINGS.env_file,
        extra='ignore'
    )


DB_SETTINGS = DatabaseSettings()
