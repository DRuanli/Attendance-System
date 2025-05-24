# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from config import settings
from app.api.routes import students, attendance, reports
from app.models.database import Base, engine

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
    yield
    # Shutdown
    logger.info("Shutting down Classroom Attendance System")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
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

@app.get("/")
async def root():
    return {
        "message": "Classroom Attendance System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
