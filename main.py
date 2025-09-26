"""
Main FastAPI application file.
Integrates all routers and initializes the application.
File: main.py
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import connect_to_mongodb, disconnect_from_mongodb
from routers.value_set_router import router as value_set_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting up Value Set Management System...")
    try:
        # Connect to MongoDB
        await connect_to_mongodb()
        logger.info("Successfully connected to MongoDB")

        # Log startup information
        logger.info(f"Application started at {datetime.utcnow().isoformat()}")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

        yield

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    finally:
        # Shutdown
        logger.info("Shutting down Value Set Management System...")
        await disconnect_from_mongodb()
        logger.info("Disconnected from MongoDB")
        logger.info(f"Application stopped at {datetime.utcnow().isoformat()}")


# Create FastAPI application
app = FastAPI(
    title="Value Set Management System",
    description="Enterprise-grade Value Set Management API for managing reusable enumerations with multilingual support",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle uncaught exceptions globally.

    Args:
        request: FastAPI request
        exc: Exception that occurred

    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": str(exc) if os.getenv("ENVIRONMENT") == "development" else None
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Root health check endpoint.

    Returns:
        Application health status
    """
    return {
        "status": "healthy",
        "application": "Value Set Management System",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        API information and available endpoints
    """
    return {
        "application": "Value Set Management System",
        "version": "1.0.0",
        "description": "Enterprise Value Set Management API",
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": "/api/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "value_sets": "/api/v1/value-sets"
        },
        "features": [
            "Multilingual support (English, Hindi)",
            "Bulk operations",
            "Archive/Restore functionality",
            "Export/Import capabilities",
            "Advanced search",
            "Audit trail",
            "Validation framework"
        ]
    }


# API version endpoint
@app.get("/api/v1")
async def api_version():
    """
    API version information.

    Returns:
        API version details
    """
    return {
        "version": "1.0.0",
        "status": "stable",
        "modules": ["value_sets"],
        "capabilities": {
            "value_sets": {
                "operations": 24,
                "bulk_support": True,
                "multilingual": True,
                "max_items_per_set": 500,
                "supported_languages": ["en", "hi"]
            }
        }
    }


# Include routers
app.include_router(value_set_router)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests and responses.

    Args:
        request: FastAPI request
        call_next: Next middleware or endpoint

    Returns:
        Response from endpoint
    """
    start_time = datetime.utcnow()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = (datetime.utcnow() - start_time).total_seconds()

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Time: {process_time:.3f}s"
    )

    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-API-Version"] = "1.0.0"

    return response


# Startup message
@app.on_event("startup")
async def startup_message():
    """
    Display startup message.
    """
    logger.info("=" * 60)
    logger.info("Value Set Management System - v1.0.0")
    logger.info("=" * 60)
    logger.info("API Documentation available at:")
    logger.info("  - Swagger UI: http://localhost:8000/api/docs")
    logger.info("  - ReDoc: http://localhost:8000/api/redoc")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    workers = int(os.getenv("WORKERS", 1))

    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Workers: {workers}")
    logger.info(f"Auto-reload: {reload}")

    # Run the application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        log_level="info",
        access_log=True
    )