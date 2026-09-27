from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Project Report Generator"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "sqlite:///./storage/app.db"
    jwt_secret: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24
    gemini_api_key: str | None = None
    gemini_generation_model: str = "gemini-3.5-flash-lite"
    gemini_fallback_models: str = "gemini-3.5-flash"
    gemini_max_retries: int = 2
    gemini_retry_delay_seconds: float = 1.5
    gemini_embedding_model: str = "gemini-embedding-001"
    storage_backend: str = "local"
    local_storage_path: str = "storage"
    chroma_path: str = "storage/chroma"
    max_upload_mb: int = 25
    allowed_upload_extensions: str = ".py,.js,.jsx,.ts,.tsx,.java,.cs,.cpp,.c,.php,.rb,.go,.rs,.sql,.html,.css,.json,.md,.txt,.pdf,.docx,.png,.jpg,.jpeg,.webp"
    render_base_url: str | None = None
    kroki_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("database_url")
    @classmethod
    def normalize_render_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def storage_path(self) -> Path:
        return Path(self.local_storage_path)

    @property
    def upload_extensions(self) -> set[str]:
        return {ext.strip().lower() for ext in self.allowed_upload_extensions.split(",") if ext.strip()}

    @property
    def generation_models(self) -> list[str]:
        models = [self.gemini_generation_model]
        models.extend(model.strip() for model in self.gemini_fallback_models.split(",") if model.strip())
        return list(dict.fromkeys(models))


@lru_cache
def get_settings() -> Settings:
    return Settings()
