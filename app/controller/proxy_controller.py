# Equivalent of ProxyController.java
# Catches all routes under /proxy/**, supports GET/POST/PUT/DELETE/PATCH.
# Also exposes /proxy/clear to flush the Redis cache.

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models import UIBean
from app.service.proxy_service import proxy_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proxy")


@router.api_route(
    "/clear",
    methods=["GET"],
    summary="Clear all cached responses from Redis",
)
async def clear_cache():
    """Equivalent of ProxyController.clearCache()"""
    proxy_service.clear_cache()

    response = UIBean(
        data=None,
        success=True,
        message="Cache cleared successfully",
        response="Cleared",
    )
    return JSONResponse(content=response.model_dump())


@router.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    summary="Forward request to upstream origin server",
)
async def proxy_request(request: Request, full_path: str):
    """
    Equivalent of ProxyController.proxyRequest().
    Reads the raw body (if any), delegates to ProxyService, returns UIBean envelope.
    """
    body = await request.body()
    method = request.method

    result: UIBean = await proxy_service.forward_request(
        method=method,
        request=request,
        body=body if body else None,
    )

    status_code = 200 if result.success else 500
    return JSONResponse(content=result.model_dump(), status_code=status_code)
