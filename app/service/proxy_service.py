# Equivalent of ProxyService.java
# Handles cache-check, upstream forwarding, header copying, and cache write.

import logging
from typing import Any

import httpx
from fastapi import Request

from app.models import UIBean
from app.service.redis_service import redis_service
from app.util.origin_holder import origin_holder

logger = logging.getLogger(__name__)

# Headers to strip before forwarding (equivalent of copyHeaders() exclusions)
EXCLUDED_HEADERS = {"host", "accept-encoding", "content-encoding"}


class ProxyService:

    def _build_cache_key(self, method: str, path: str, query: str | None) -> str:
        key = f"{method.upper()}:{path}?{query or ''}"
        logger.info("Cache key: %s", key)
        return key

    def _build_upstream_url(self, path: str, query: str | None) -> str:
        # Strip the /proxy prefix — equivalent of replaceFirst("/proxy", "")
        path_without_prefix = path.removeprefix("/proxy")
        origin = origin_holder.get_origin()
        url = origin + path_without_prefix
        if query:
            url += f"?{query}"
        logger.info("Final upstream URL: %s", url)
        return url

    def _copy_headers(self, request: Request) -> dict[str, str]:
        """Copy request headers, excluding host/encoding headers."""
        return {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in EXCLUDED_HEADERS
        }

    async def forward_request(
        self,
        method: str,
        request: Request,
        body: bytes | None,
    ) -> UIBean:

        path = request.url.path
        query = request.url.query or None
        cache_key = self._build_cache_key(method, path, query)

        # Cache check for GET requests
        if method.upper() == "GET":
            cached = redis_service.get(cache_key, UIBean)
            if cached is not None:
                cached.success = True
                cached.message = "Cache Hit"
                logger.info("Cache Hit for key: %s", cache_key)
                return cached

        upstream_url = self._build_upstream_url(path, query)
        headers = self._copy_headers(request)

        try:
            async with httpx.AsyncClient() as client:
                logger.info("Sending upstream request with method: %s", method)

                upstream_response = await client.request(
                    method=method.upper(),
                    url=upstream_url,
                    headers=headers,
                    content=body if body else None,
                )

            # Validate content type — must be application/json
            content_type = upstream_response.headers.get("content-type", "")
            if "application/json" not in content_type:
                error = UIBean(
                    success=False,
                    message="Invalid content type from upstream",
                    response=f"Expected application/json but got {content_type}",
                )
                return error

            data: Any = upstream_response.json()
            logger.info("Response from upstream: %s", data)

            response = UIBean(
                data=data,
                success=True,
                message="Cache Miss",
                response="Upstream call successful",
            )

            # Cache the response (all methods, matching original Java behavior)
            redis_service.save(cache_key, response.model_dump())

            return response

        except Exception as ex:
            logger.exception("Upstream call failed")
            return UIBean(
                success=False,
                message="Upstream call failed",
                response=str(ex),
            )

    def clear_cache(self) -> None:
        logger.info("Clearing all cache...")
        redis_service.clear_all()
        logger.info("Cache cleared")


# Single shared instance
proxy_service = ProxyService()
