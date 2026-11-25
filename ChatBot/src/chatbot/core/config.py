from functools import lru_cache
from pathlib import Path

import boto3
from botocore.client import BaseClient
from langchain_ollama import ChatOllama
from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


_SETTINGS_CONFIG = SettingsConfigDict(
    env_file=Path(__file__).resolve().parents[4] / ".env",
    env_file_encoding="utf-8",
    extra="ignore",
    case_sensitive=False,
)


class Settings(BaseSettings):
    model_config = _SETTINGS_CONFIG
# Config for the Postgres database connection and Ollama LLM client.
    db_host: str = "localhost"
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = "chatbot"
    db_user: str = "chatbot"
    db_password: SecretStr = Field(validation_alias=AliasChoices("DB_PASSWORD", "POSTGRES_PASSWORD"))

# Config for the Ollama LLM client.
    ollama_model: str = "qwen3-vi:latest"
    ollama_base_url: str = "http://localhost:11434"

# Config for the S3-compatible bucket (Cloudflare R2) for storing files.
    r2_bucket: str
    r2_endpoint: str
    r2_access_key_id: str
    r2_secret_access_key: SecretStr

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_r2_client() -> BaseClient:
    """Return an S3-compatible client configured for Cloudflare R2."""
    settings = get_settings()
    return boto3.client(
        service_name="s3",
        endpoint_url=settings.r2_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key.get_secret_value(),
        region_name="auto",
    )


@lru_cache
def get_llm(reasoning: bool = False) -> ChatOllama:
    """Return a configured Ollama client with the requested thinking mode."""
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        reasoning=reasoning,
        client_kwargs={"timeout": 180},
    )
