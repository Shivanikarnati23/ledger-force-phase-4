from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    database_url: str = "sqlite:///./ledger.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()