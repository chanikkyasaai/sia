"""
Redis cache service for business snapshots and quick data access
"""
import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Initialize Redis connection"""
        try:
            # Use simple Redis connection without SSL parameters that might be incompatible
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None

    async def get_business_snapshot(self, business_id: int) -> Optional[Dict[str, Any]]:
        """Get business snapshot from cache"""
        if not self.redis_client:
            return None

        try:
            key = f"business_snapshot:{business_id}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(
                f"Failed to get business snapshot for {business_id}: {e}")

        return None

    async def set_business_snapshot(self, business_id: int, snapshot: Dict[str, Any], ttl_seconds: int = 300):
        """Set business snapshot in cache with TTL"""
        if not self.redis_client:
            return False

        try:
            key = f"business_snapshot:{business_id}"
            snapshot["last_updated"] = datetime.utcnow().isoformat()
            await self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(snapshot, default=str)
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to set business snapshot for {business_id}: {e}")
            return False

    async def invalidate_business_snapshot(self, business_id: int):
        """Invalidate business snapshot cache"""
        if not self.redis_client:
            return

        try:
            key = f"business_snapshot:{business_id}"
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(
                f"Failed to invalidate snapshot for {business_id}: {e}")

    async def get_customer_cache(self, business_id: int, customer_key: str) -> Optional[Dict[str, Any]]:
        """Get customer data from cache"""
        if not self.redis_client:
            return None

        try:
            key = f"customer:{business_id}:{customer_key}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get customer cache: {e}")

        return None

    async def set_customer_cache(self, business_id: int, customer_key: str, customer_data: Dict[str, Any], ttl_seconds: int = 1800):
        """Set customer data in cache"""
        if not self.redis_client:
            return False

        try:
            key = f"customer:{business_id}:{customer_key}"
            await self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(customer_data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set customer cache: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()


# Global cache service instance
cache_service = CacheService()
