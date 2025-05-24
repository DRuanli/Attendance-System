# app/services/attendance_service.py
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import numpy as np
from app.core import FaceRecognitionSystem, CameraHandler
from app.models import Student, Attendance, Classroom, Enrollment
import logging

logger = logging.getLogger(__name__)


class AttendanceService:
    def __init__(self):
        self.face_recognition = FaceRecognitionSystem()
        self.camera_handler = CameraHandler()
        self.processed_today = set()  # Track students already marked today

    def start_attendance_session(self, classroom_id: int, db: Session):
        """Start attendance tracking for a classroom."""
        # Load enrolled students
        enrollments = db.query(Enrollment).filter(
            Enrollment.classroom_id == classroom_id
        ).all()

        students = []
        for enrollment in enrollments:
            student = enrollment.student
            if student.face_encoding and student.is_active:
                students.append({
                    'id': student.id,
                    'full_name': student.full_name,
                    'face_encoding': student.face_encoding
                })

        # Load known faces
        self.face_recognition.load_known_faces(students)

        # Start camera
        self.camera_handler.start()

        # Reset daily tracking
        today = date.today()
        self.processed_today = set(
            a.student_id for a in db.query(Attendance).filter(
                Attendance.classroom_id == classroom_id,
                Attendance.check_in_time >= datetime.combine(today, time.min)
            ).all()
        )

        logger.info(f"Started attendance session for classroom {classroom_id}")

    def stop_attendance_session(self):
        """Stop attendance tracking."""
        self.camera_handler.stop()
        logger.info("Stopped attendance session")

    async def process_attendance_frame(self, classroom_id: int, db: Session):
        """Process a single frame for attendance."""
        # Get frame from camera
        frame = self.camera_handler.get_frame()
        if frame is None:
            return []

        # Get classroom info
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            return []

        # Process frame
        _, results = self.face_recognition.process_frame(frame)

        marked_students = []

        for result in results:
            student_id = result.get('student_id')

            # Skip if unknown or already processed today
            if not student_id or student_id in self.processed_today:
                continue

            # Determine attendance status
            now = datetime.now()
            class_start = datetime.combine(now.date(), classroom.start_time)
            late_threshold = class_start + timedelta(minutes=classroom.late_threshold_minutes)

            status = "present"
            if now > late_threshold:
                status = "late"

            # Mark attendance
            attendance = Attendance(
                student_id=student_id,
                classroom_id=classroom_id,
                confidence_score=result['confidence'],
                status=status,
                is_verified=result['confidence'] >= 0.85
            )

            db.add(attendance)
            db.commit()

            # Add to processed set
            self.processed_today.add(student_id)

            marked_students.append({
                'student_name': result['name'],
                'status': status,
                'confidence': result['confidence'],
                'time': now
            })

            logger.info(f"Marked attendance for {result['name']} - {status}")

        return marked_students

    def get_absentees(self, classroom_id: int, db: Session) -> List[Dict]:
        """Get list of absent students for today."""
        today = date.today()

        # Get all enrolled students
        enrolled_ids = db.query(Enrollment.student_id).filter(
            Enrollment.classroom_id == classroom_id
        ).subquery()

        # Get students who attended today
        attended_ids = db.query(Attendance.student_id).filter(
            Attendance.classroom_id == classroom_id,
            Attendance.check_in_time >= datetime.combine(today, time.min)
        ).subquery()

        # Find absentees
        absentees = db.query(Student).filter(
            Student.id.in_(enrolled_ids),
            ~Student.id.in_(attended_ids),
            Student.is_active == True
        ).all()

        return [
            {
                'student_id': s.student_id,
                'name': s.full_name,
                'email': s.email
            }
            for s in absentees
        ]
