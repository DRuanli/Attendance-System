# app/core/background_service.py
import asyncio
import signal
import logging
from typing import Optional
from app.services.scheduler_service import AttendanceSchedulerService
from sqlalchemy.orm import Session
from config.database import SessionLocal
import threading

logger = logging.getLogger(__name__)


class BackgroundServiceManager:
    """Manages all background services for automatic attendance."""

    def __init__(self):
        self.scheduler_service = AttendanceSchedulerService()
        self.is_running = False
        self.main_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Start all background services."""
        if self.is_running:
            logger.warning("Background services already running")
            return

        self.is_running = True
        logger.info("Starting background services...")

        # Initialize scheduler
        self.scheduler_service.initialize()

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self.shutdown)

        # Start monitoring task
        self.main_task = asyncio.create_task(self._monitor_services())

        logger.info("Background services started successfully")

    async def shutdown(self):
        """Gracefully shutdown all services."""
        logger.info("Shutting down background services...")
        self.is_running = False

        # Stop scheduler
        self.scheduler_service.shutdown()

        # Signal shutdown
        self._shutdown_event.set()

        # Wait for main task to complete
        if self.main_task:
            await asyncio.gather(self.main_task, return_exceptions=True)

        logger.info("Background services shutdown complete")

    async def _monitor_services(self):
        """Monitor and maintain background services."""
        while self.is_running:
            try:
                # Check active sessions
                active_sessions = self.scheduler_service.get_active_sessions()

                if active_sessions:
                    logger.debug(f"Active attendance sessions: {len(active_sessions)}")

                # Check for any issues and restart if needed
                await self._health_check()

                # Wait for 30 seconds or shutdown signal
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=30.0
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Continue monitoring

            except Exception as e:
                logger.error(f"Error in background service monitor: {e}")
                await asyncio.sleep(5)

    async def _health_check(self):
        """Perform health checks on services."""
        # Check database connection
        try:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        # Check camera connections
        for camera_key, camera in self.scheduler_service.camera_handler.cameras.items():
            if not camera.is_connected():
                logger.warning(f"Camera {camera_key} disconnected, attempting reconnect...")

    def get_status(self) -> dict:
        """Get current status of background services."""
        return {
            'running': self.is_running,
            'scheduler': {
                'active_sessions': self.scheduler_service.get_active_sessions(),
                'jobs': [
                    {
                        'id': job.id,
                        'next_run': str(job.next_run_time),
                        'trigger': str(job.trigger)
                    }
                    for job in self.scheduler_service.scheduler.get_jobs()
                ]
            },
            'cameras': {
                camera_key: {
                    'connected': camera.is_connected(),
                    'type': camera.config.camera_type.value,
                    'location': camera.config.location
                }
                for camera_key, camera in self.scheduler_service.camera_handler.cameras.items()
            }
        }


# Singleton instance
background_service = BackgroundServiceManager()


async def start_background_services():
    """Start background services (called from main.py)."""
    await background_service.start()


async def stop_background_services():
    """Stop background services (called from main.py)."""
    await background_service.shutdown()