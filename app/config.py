# Equivalent of ProxyConfig.java + application.properties
# Uses pydantic-settings to load config from environment variables.

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Proxy
    proxy_origin: str = Field(..., env="PROXY_ORIGIN")  # Required — app exits if missing

    # Server
    server_port: int = Field(default=8081, env="PORT")

    # Redis
    redis_host: str = Field(..., env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_database: int = Field(default=0, env="REDIS_DATABASE")
    redis_connection_timeout: int = Field(default=2000, env="REDIS_CONNECTION_TIMEOUT")

    # Redis pool
    redis_max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")

    # Cache
    cache_key_prefix: str = Field(default="CACHE_KEY", env="CACHE_KEY")
    response_ttl_days: int = Field(default=1, env="RESPONSE_TTL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Single shared instance
settings = Settings()
