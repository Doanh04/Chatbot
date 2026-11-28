from functools import lru_cache
from pathlib import Path

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableWithFallbacks
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

# Config for models served through the Gemini Developer API.
    gemini_api_key: SecretStr | None = None
    gemini_model_35_flash_lite: str = "gemini-3.5-flash-lite"
    gemini_model_31_flash_lite: str = "gemini-3.1-flash-lite"
    gemini_model_gemma_4_26b: str = "gemma-4-26b-a4b-it"
    gemini_model_gemma_4_31b: str = "gemma-4-31b-it"
    gemini_default_model: str = "gemini-3.5-flash-lite"

# Config for the S3-compatible bucket (Cloudflare R2) for storing files.
    r2_bucket: str | None = None
    r2_endpoint: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: SecretStr | None = None
    storage_dir: Path = Path(__file__).resolve().parents[3] / "storage"

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
    if not all((settings.r2_bucket, settings.r2_endpoint, settings.r2_access_key_id)) or (
        settings.r2_secret_access_key is None
        or not settings.r2_secret_access_key.get_secret_value()
    ):
        raise ValueError("R2_BUCKET, R2_ENDPOINT and R2 API keys are required to use R2")
    return boto3.client(
        service_name="s3",
        endpoint_url=settings.r2_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key.get_secret_value(),
        region_name="auto",
        config=Config(signature_version="s3v4"),
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


@lru_cache
def get_gemini_llm(model: str | None = None) -> ChatGoogleGenerativeAI:
    """Return a Gemini API client for one of the four configured models."""
    settings = get_settings()
    if settings.gemini_api_key is None or not settings.gemini_api_key.get_secret_value():
        raise ValueError("GEMINI_API_KEY is required to use Gemini models")

    configured_models = {
        settings.gemini_model_35_flash_lite,
        settings.gemini_model_31_flash_lite,
        settings.gemini_model_gemma_4_26b,
        settings.gemini_model_gemma_4_31b,
    }
    selected_model = model or settings.gemini_default_model
    if selected_model not in configured_models:
        raise ValueError(f"Gemini model is not configured: {selected_model}")

    return ChatGoogleGenerativeAI(
        model=selected_model,
        api_key=settings.gemini_api_key.get_secret_value(),
    )


@lru_cache
def get_gemini_llm_with_fallbacks(model: str | None = None) -> RunnableWithFallbacks:
    """Try Gemini models in order, then use the local Ollama model on errors."""
    settings = get_settings()
    primary = get_gemini_llm(model)
    models = dict.fromkeys((
        settings.gemini_model_35_flash_lite,
        settings.gemini_model_31_flash_lite,
        settings.gemini_model_gemma_4_26b,
        settings.gemini_model_gemma_4_31b,
    ))
    fallbacks = [get_gemini_llm(name) for name in models if name != primary.model]
    fallbacks.append(get_llm())
    return primary.with_fallbacks(fallbacks)
