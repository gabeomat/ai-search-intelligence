"""System configuration management."""

from typing import List, Optional
from pydantic import BaseSettings, Field, validator
import os
from functools import lru_cache


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    url: str = Field(..., env="DATABASE_URL")
    echo: bool = Field(False, env="DATABASE_ECHO")
    pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(20, env="DATABASE_MAX_OVERFLOW")


class RedisConfig(BaseSettings):
    """Redis configuration."""
    url: str = Field(..., env="REDIS_URL")
    max_connections: int = Field(100, env="REDIS_MAX_CONNECTIONS")


class InfluxDBConfig(BaseSettings):
    """InfluxDB configuration for time-series data."""
    url: str = Field(..., env="INFLUXDB_URL")
    token: str = Field(..., env="INFLUXDB_TOKEN")
    org: str = Field(..., env="INFLUXDB_ORG")
    bucket: str = Field(..., env="INFLUXDB_BUCKET")


class APIKeyConfig(BaseSettings):
    """External API keys configuration."""
    serpapi_key: str = Field(..., env="SERPAPI_KEY")
    perplexity_api_key: str = Field(..., env="PERPLEXITY_API_KEY")


class SecurityConfig(BaseSettings):
    """Security configuration."""
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")


class APIConfig(BaseSettings):
    """API server configuration."""
    host: str = Field("0.0.0.0", env="API_HOST")
    port: int = Field(8000, env="API_PORT")
    debug: bool = Field(False, env="API_DEBUG")
    reload: bool = Field(False, env="API_RELOAD")
    title: str = "AI Search Intelligence API"
    description: str = "API for AI search intelligence and citation tracking"
    version: str = "0.1.0"


class CeleryConfig(BaseSettings):
    """Celery configuration."""
    broker_url: str = Field(..., env="CELERY_BROKER_URL")
    result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = ["json"]
    timezone: str = "UTC"
    enable_utc: bool = True


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration for external APIs."""
    serpapi_rate_limit: int = Field(100, env="SERPAPI_RATE_LIMIT")  # per hour
    perplexity_rate_limit: int = Field(1000, env="PERPLEXITY_RATE_LIMIT")  # per hour


class DataCollectionConfig(BaseSettings):
    """Data collection configuration."""
    default_collection_interval: int = Field(3600, env="DEFAULT_COLLECTION_INTERVAL")  # seconds
    max_queries_per_batch: int = Field(50, env="MAX_QUERIES_PER_BATCH")
    citation_retention_days: int = Field(365, env="CITATION_RETENTION_DAYS")


class AnalysisConfig(BaseSettings):
    """Content analysis configuration."""
    min_content_score_threshold: float = Field(0.5, env="MIN_CONTENT_SCORE_THRESHOLD")
    max_content_age_days: int = Field(30, env="MAX_CONTENT_AGE_DAYS")
    enable_ml_predictions: bool = Field(True, env="ENABLE_ML_PREDICTIONS")


class MonitoringConfig(BaseSettings):
    """Monitoring and logging configuration."""
    log_level: str = Field("INFO", env="LOG_LEVEL")
    prometheus_port: int = Field(8001, env="PROMETHEUS_PORT")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")


class N8NConfig(BaseSettings):
    """n8n integration configuration."""
    webhook_base_url: str = Field(..., env="N8N_WEBHOOK_BASE_URL")
    api_key: Optional[str] = Field(None, env="N8N_API_KEY")


class DevelopmentConfig(BaseSettings):
    """Development settings."""
    development_mode: bool = Field(False, env="DEVELOPMENT_MODE")
    mock_external_apis: bool = Field(False, env="MOCK_EXTERNAL_APIS")
    enable_debug_endpoints: bool = Field(False, env="ENABLE_DEBUG_ENDPOINTS")


class Settings(BaseSettings):
    """Main application settings."""
    
    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    influxdb: InfluxDBConfig = InfluxDBConfig()
    api_keys: APIKeyConfig = APIKeyConfig()
    security: SecurityConfig = SecurityConfig()
    api: APIConfig = APIConfig()
    celery: CeleryConfig = CeleryConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()
    data_collection: DataCollectionConfig = DataCollectionConfig()
    analysis: AnalysisConfig = AnalysisConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    n8n: N8NConfig = N8NConfig()
    development: DevelopmentConfig = DevelopmentConfig()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("database", pre=True, always=True)
    def validate_database_config(cls, v):
        if isinstance(v, dict):
            return DatabaseConfig(**v)
        return v or DatabaseConfig()

    @validator("redis", pre=True, always=True)
    def validate_redis_config(cls, v):
        if isinstance(v, dict):
            return RedisConfig(**v)
        return v or RedisConfig()


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()