from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, EmailStr, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "FastAPI App"
    APP_ENV: Literal["local", "staging", "production"] = "local"
    APP_KEY: str
    APP_DEBUG: bool = False
    APP_URL: AnyHttpUrl = "http://localhost:8000"  # type: ignore[assignment]
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DB_CONNECTION: Literal["mysql", "postgres"] = "mysql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_DATABASE: str
    DB_USERNAME: str
    DB_PASSWORD: str

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        if self.DB_CONNECTION == "postgres":
            return (
                f"postgresql+asyncpg://{self.DB_USERNAME}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
            )
        return (
            f"mysql+aiomysql://{self.DB_USERNAME}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        )

    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        if self.DB_CONNECTION == "postgres":
            return (
                f"postgresql+psycopg2://{self.DB_USERNAME}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
            )
        return (
            f"mysql+pymysql://{self.DB_USERNAME}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        )

    # Authentication & Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS & Security
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS_RAW: str = "http://localhost:3000"

    @computed_field
    @property
    def CORS_ORIGINS(self) -> list[str]:
        if isinstance(self.CORS_ORIGINS_RAW, str):
            return [
                origin.strip()
                for origin in self.CORS_ORIGINS_RAW.split(",")
                if origin.strip()
            ]
        return self.CORS_ORIGINS_RAW

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return list({self.FRONTEND_URL, *self.CORS_ORIGINS})

    # Superuser
    FIRST_SUPERUSER: EmailStr = "admin@example.com"  # type: ignore[assignment]
    FIRST_SUPERUSER_PASSWORD: str

    # Logging
    LOG_LEVEL: str = "debug"
    LOG_FORMAT: Literal["json", "console"] = "console"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Mail
    MAIL_MAILER: str = "smtp"
    MAIL_HOST: str | None = None
    MAIL_PORT: int = 1025
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_ENCRYPTION: str | None = None
    MAIL_FROM_ADDRESS: EmailStr = "noreply@example.com"  # type: ignore[assignment]
    MAIL_FROM_NAME: str = "App"

    @computed_field
    @property
    def mail_enabled(self) -> bool:
        return self.MAIL_HOST is not None

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @computed_field
    @property
    def is_debug(self) -> bool:
        return self.APP_DEBUG


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
