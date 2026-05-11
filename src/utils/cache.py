"""Redis cache utilities (optional)."""

from __future__ import annotations

from typing import Any

import redis.asyncio as redis

from config.settings import get_settings


async def get_redis() -> redis.Redis:
    settings = get_settings()
    return redis.from_url(settings.redis_url, decode_responses=True)


async def cache_get(client: redis.Redis, key: str) -> str | None:
    return await client.get(key)


async def cache_set(client: redis.Redis, key: str, value: str, ttl_sec: int = 300) -> Any:
    return await client.set(key, value, ex=ttl_sec)
