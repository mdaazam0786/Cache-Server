# Equivalent of RedisService.java + RedisServiceImpl.java + RedisConfig.java
# Uses redis-py with a connection pool (equivalent of Jedis pool config).

import json
import logging
from typing import Any, Type, TypeVar

import redis

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RedisService:
    def __init__(self):
        # Connection pool — equivalent of JedisPoolConfig
        pool = redis.ConnectionPool(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_database,
            socket_connect_timeout=settings.redis_connection_timeout / 1000,  # ms -> seconds
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
        self._client = redis.Redis(connection_pool=pool)
        self._ttl_seconds = settings.response_ttl_days * 86400  # days -> seconds
        self._prefix = settings.cache_key_prefix

    def save(self, key: str, value: Any) -> None:
        """Serialize value to JSON and store in Redis with TTL."""
        try:
            serialized = json.dumps(value)
            full_key = self._prefix + key
            self._client.setex(full_key, self._ttl_seconds, serialized)
            logger.info("Response saved successfully...")
        except Exception as e:
            logger.error("Error while saving response in cache: %s", e)

    def get(self, key: str, clazz: Type[T]) -> T | None:
        """Fetch from Redis and deserialize into the given type."""
        if not key:
            logger.info("Key cannot be empty or null")
            return None
        try:
            full_key = self._prefix + key
            raw = self._client.get(full_key)
            if raw is None:
                logger.info("Cache Miss")
                return None
            data = json.loads(raw)
            # If clazz is a Pydantic model, parse it; otherwise return raw dict
            if hasattr(clazz, "model_validate"):
                return clazz.model_validate(data)
            return clazz(data)
        except Exception as e:
            logger.error("Error while fetching the response: %s", e)
            return None

    def clear_all(self) -> None:
        """Flush the entire Redis database — equivalent of flushAll()."""
        try:
            self._client.flushall()
            logger.info("Redis flushed successfully")
        except Exception as e:
            logger.error("Error while clearing cache: %s", e)


# Single shared instance
redis_service = RedisService()
