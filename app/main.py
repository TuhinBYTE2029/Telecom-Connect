"""Main application entrypoint for Telecom Connect."""
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import check_db_connection, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: handle startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    # Initialize DB tables (creates them if not existing)
    init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Prepaid mobile plan comparison and recharge platform for "
            "Telecom Connect (Ahmedabad, Gujarat)."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    cors_origins = (
        settings.CORS_ORIGINS
        if isinstance(settings.CORS_ORIGINS, list)
        else [str(settings.CORS_ORIGINS)]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register centralized exception handlers
    register_exception_handlers(app)

    # Root endpoint
    @app.get("/", tags=["General"])
    async def root() -> Dict[str, Any]:
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "city": "Ahmedabad",
            "status": "operational",
            "documentation": "/docs",
        }

    # Health check endpoint
    @app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
    async def health_check() -> Dict[str, Any]:
        db_alive = check_db_connection()
        return {
            "status": "healthy" if db_alive else "degraded",
            "environment": settings.APP_ENV,
            "services": {
                "database": "reachable" if db_alive else "unreachable",
                "api": "operational",
            },
        }

    # Register API routers
    from app.api.v1.api_router import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
