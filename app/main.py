# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import asyncio
from config import settings
from app.api.routes import students, attendance, reports, scheduler
from config.database import Base, engine
from app.core.background_service import start_background_services, stop_background_services

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Classroom Attendance System")

    # Start background services if enabled
    if settings.enable_background_service:
        logger.info("Starting background services...")
        await start_background_services()

    yield

    # Shutdown
    logger.info("Shutting down Classroom Attendance System")

    # Stop background services
    if settings.enable_background_service:
        logger.info("Stopping background services...")
        await stop_background_services()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Automatic Classroom Attendance System with Face Recognition",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(students.router, prefix=f"{settings.api_prefix}/students", tags=["Students"])
app.include_router(attendance.router, prefix=f"{settings.api_prefix}/attendance", tags=["Attendance"])
app.include_router(reports.router, prefix=f"{settings.api_prefix}/reports", tags=["Reports"])
app.include_router(scheduler.router, prefix=f"{settings.api_prefix}/scheduler", tags=["Scheduler"])


@app.get("/")
async def root():
    return {
        "message": "Classroom Attendance System API",
        "version": "2.0.0",
        "features": {
            "face_recognition": "FaceNet",
            "multi_camera": settings.enable_ip_cameras,
            "auto_scheduling": settings.enable_auto_scheduling,
            "background_service": settings.enable_background_service
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status."""
    health_status = {
        "status": "healthy",
        "database": "connected",
        "background_service": "inactive"
    }

    # Check database
    try:
        from config.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check background service
    if settings.enable_background_service:
        try:
            from app.core.background_service import background_service
            service_status = background_service.get_status()
            health_status["background_service"] = "active" if service_status["running"] else "inactive"
            health_status["active_sessions"] = len(service_status["scheduler"]["active_sessions"])
        except Exception as e:
            health_status["background_service"] = f"error: {str(e)}"

    return health_status


@app.get("/system/info")
async def system_info():
    """Get system information and configuration."""
    from app.core.background_service import background_service

    return {
        "settings": {
            "auto_scheduling": settings.enable_auto_scheduling,
            "ip_cameras": settings.enable_ip_cameras,
            "background_service": settings.enable_background_service,
            "min_detections": settings.min_detections_required,
            "track_timeout": settings.track_timeout_seconds,
            "confidence_threshold": settings.confidence_threshold
        },
        "service_status": background_service.get_status() if settings.enable_background_service else None
    }