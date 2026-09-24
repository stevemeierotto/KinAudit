from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://kinaudit:kinaudit@localhost:5432/kinaudit"
    environment: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
