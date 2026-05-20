# Equivalent of ProxyServerApplication.java + StartupConfigLoader.java
# Initializes FastAPI, validates required config at startup,
# sets the origin in OriginHolder, and registers the proxy router.

import logging
import sys

import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.controller.proxy_controller import router as proxy_router
from app.util.origin_holder import origin_holder

# Logging setup — mirrors Spring Boot's default logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Caching Proxy Server",
        description="HTTP caching proxy — forwards requests to an origin and caches responses in Redis.",
        version="0.0.1",
    )

    # Startup event — equivalent of StartupConfigLoader.run()
    @app.on_event("startup")
    async def startup():
        if not settings.proxy_origin:
            logger.error("Missing required origin (PROXY_ORIGIN)")
            sys.exit(1)

        origin_holder.set_origin(settings.proxy_origin)
        logger.info("Origin set to: %s", origin_holder.get_origin())

    # Register routes
    app.include_router(proxy_router)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.server_port,
        reload=False,
    )
