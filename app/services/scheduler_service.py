# app/services/scheduler_service.py
import asyncio
from datetime import datetime, time, timedelta, date
from typing import Dict, List, Optional
import logging
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.models import Classroom, Enrollment
from app.services.attendance_service import AttendanceService
from app.core.camera_handler import MultiCameraHandler, CameraConfig, CameraType
from config.database import SessionLocal
import json

logger = logging.getLogger(__name__)


class AttendanceSchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.attendance_service = AttendanceService()
        self.camera_handler = MultiCameraHandler()
        self.active_sessions: Dict[int, Dict] = {}
        self.camera_configs: Dict[int, List[CameraConfig]] = {}

    def initialize(self):
        """Initialize the scheduler and load configurations."""
        self._load_camera_configurations()
        self._setup_classroom_schedules()
        self.scheduler.start()
        logger.info("Attendance scheduler initialized")

    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        self.camera_handler.stop_all()
        logger.info("Attendance scheduler shutdown")

    def _load_camera_configurations(self):
        """Load camera configurations from database or config file."""
        # Default camera configurations
        default_configs = {
            1: [  # Classroom ID 1
                CameraConfig(
                    camera_id=0,
                    camera_type=CameraType.USB,
                    name="instructor_cam",
                    location="front",
                    fps=10
                ),
                CameraConfig(
                    camera_id="192.168.1.100:554/stream1",
                    camera_type=CameraType.RTSP,
                    name="security_cam_1",
                    location="back_left",
                    username="admin",
                    password="admin123",
                    fps=15
                ),
                CameraConfig(
                    camera_id="192.168.1.101:554/stream1",
                    camera_type=CameraType.RTSP,
                    name="security_cam_2",
                    location="back_right",
                    username="admin",
                    password="admin123",
                    fps=15
                )
            ]
        }

        # Load from config file if exists
        try:
            with open('config/camera_config.json', 'r') as f:
                loaded_configs = json.load(f)
                for classroom_id, configs in loaded_configs.items():
                    self.camera_configs[int(classroom_id)] = [
                        CameraConfig(**config) for config in configs
                    ]
        except FileNotFoundError:
            self.camera_configs = default_configs
            logger.info("Using default camera configurations")

    def _setup_classroom_schedules(self):
        """Setup automatic attendance sessions based on classroom schedules."""
        db = SessionLocal()
        try:
            classrooms = db.query(Classroom).filter(Classroom.is_active == True).all()

            for classroom in classrooms:
                if classroom.day_of_week is not None and classroom.start_time:
                    # Calculate start time (5 minutes early)
                    start_hour = classroom.start_time.hour
                    start_minute = classroom.start_time.minute - 5

                    # Handle negative minutes
                    if start_minute < 0:
                        start_minute += 60
                        start_hour -= 1
                        if start_hour < 0:
                            start_hour = 23

                    # Schedule start of attendance session
                    start_trigger = CronTrigger(
                        day_of_week=classroom.day_of_week,
                        hour=start_hour,
                        minute=start_minute
                    )

                    self.scheduler.add_job(
                        self._start_attendance_session,
                        trigger=start_trigger,
                        args=[classroom.id],
                        id=f"start_classroom_{classroom.id}",
                        replace_existing=True
                    )

                    # Schedule end of attendance session
                    if classroom.end_time:
                        # Calculate end time (10 minutes after class)
                        end_hour = classroom.end_time.hour
                        end_minute = classroom.end_time.minute + 10

                        # Handle minute overflow
                        if end_minute >= 60:
                            end_minute -= 60
                            end_hour += 1
                            if end_hour >= 24:
                                end_hour = 0

                        end_trigger = CronTrigger(
                            day_of_week=classroom.day_of_week,
                            hour=end_hour,
                            minute=end_minute
                        )

                        self.scheduler.add_job(
                            self._stop_attendance_session,
                            trigger=end_trigger,
                            args=[classroom.id],
                            id=f"stop_classroom_{classroom.id}",
                            replace_existing=True
                        )

                    logger.info(f"Scheduled attendance for classroom {classroom.course_name}")

        finally:
            db.close()

    async def _start_attendance_session(self, classroom_id: int):
        """Start automatic attendance session for a classroom."""
        logger.info(f"Starting automatic attendance for classroom {classroom_id}")

        # Initialize cameras for this classroom
        if classroom_id in self.camera_configs:
            for config in self.camera_configs[classroom_id]:
                camera_key = self.camera_handler.add_camera(config)

        self.camera_handler.start_all()

        # Initialize attendance service
        db = SessionLocal()
        try:
            self.attendance_service.start_attendance_session(classroom_id, db)

            # Create session info
            self.active_sessions[classroom_id] = {
                'start_time': datetime.now(),
                'processed_count': 0,
                'cameras': list(self.camera_handler.cameras.keys()),
                'processing_task': asyncio.create_task(
                    self._process_attendance_continuous(classroom_id)
                )
            }

        finally:
            db.close()

    async def _stop_attendance_session(self, classroom_id: int):
        """Stop automatic attendance session for a classroom."""
        logger.info(f"Stopping automatic attendance for classroom {classroom_id}")

        if classroom_id in self.active_sessions:
            # Cancel processing task
            session = self.active_sessions[classroom_id]
            if 'processing_task' in session:
                session['processing_task'].cancel()

            # Stop cameras
            for camera_key in session.get('cameras', []):
                self.camera_handler.remove_camera(camera_key)

            # Generate session report
            await self._generate_session_report(classroom_id, session)

            del self.active_sessions[classroom_id]

        self.attendance_service.stop_attendance_session()

    async def _process_attendance_continuous(self, classroom_id: int):
        """Continuously process frames for attendance."""
        process_interval = 3  # Process frames every 3 seconds

        while classroom_id in self.active_sessions:
            try:
                # Get frames from all cameras
                frames = self.camera_handler.get_all_frames()

                if frames:
                    db = SessionLocal()
                    try:
                        # Process each camera frame
                        for camera_key, frame in frames.items():
                            marked_students = await self.attendance_service.process_frame_with_tracking(
                                frame, classroom_id, db, camera_key
                            )

                            if marked_students:
                                self.active_sessions[classroom_id]['processed_count'] += len(marked_students)
                                logger.info(f"Marked {len(marked_students)} students from {camera_key}")

                    finally:
                        db.close()

                await asyncio.sleep(process_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing attendance: {e}")
                await asyncio.sleep(process_interval)

    async def _generate_session_report(self, classroom_id: int, session_info: Dict):
        """Generate attendance report for the session."""
        db = SessionLocal()
        try:
            from app.services.report_service import ReportService
            report_service = ReportService()

            # Get today's attendance summary
            summary = report_service.get_daily_summary(classroom_id, date.today(), db)

            duration = datetime.now() - session_info['start_time']

            logger.info(f"""
            Attendance Session Report - Classroom {classroom_id}
            Duration: {duration}
            Total Processed: {session_info['processed_count']}
            Present: {summary['present']}
            Late: {summary['late']}
            Absent: {summary['absent']}
            Attendance Rate: {summary['attendance_rate']}%
            """)

            # Send notifications for absentees if configured
            if summary['absent'] > 0:
                absentees = self.attendance_service.get_absentees(classroom_id, db)
                # TODO: Implement notification service

        finally:
            db.close()

    def add_manual_session(self, classroom_id: int, duration_minutes: int = 120):
        """Add a manual attendance session outside of regular schedule."""
        end_time = datetime.now() + timedelta(minutes=duration_minutes)

        # Start session immediately
        asyncio.create_task(self._start_attendance_session(classroom_id))

        # Schedule end
        self.scheduler.add_job(
            self._stop_attendance_session,
            trigger='date',
            run_date=end_time,
            args=[classroom_id],
            id=f"manual_stop_{classroom_id}_{datetime.now().timestamp()}"
        )

        logger.info(f"Added manual session for classroom {classroom_id} for {duration_minutes} minutes")

    def get_active_sessions(self) -> Dict[int, Dict]:
        """Get information about active attendance sessions."""
        return {
            classroom_id: {
                'start_time': session['start_time'].isoformat(),
                'duration': str(datetime.now() - session['start_time']),
                'processed_count': session['processed_count'],
                'cameras': session['cameras']
            }
            for classroom_id, session in self.active_sessions.items()
        }