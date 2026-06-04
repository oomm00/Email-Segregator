from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: str = "*"
    service_name: str = "shipping-email"

    # Database
    database_url: str = "postgresql+asyncpg://shipping:shipping_secret@localhost:5432/shipping_email"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery / RabbitMQ
    celery_broker_url: str = "amqp://shipping:shipping_secret@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Elasticsearch
    elasticsearch_hosts: str = "http://localhost:9200"
    elasticsearch_verify_certs: bool = False

    # JWT
    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "shipping_access"
    minio_secret_key: str = "shipping_secret"
    minio_bucket: str = "shipping-attachments"
    minio_secure: bool = False
    minio_region: Optional[str] = None

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
