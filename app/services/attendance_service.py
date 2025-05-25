# app/services/attendance_service.py
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Set, Tuple
import numpy as np
from collections import defaultdict
import logging
from app.core import FaceRecognitionSystem
from app.models import Student, Attendance, Classroom, Enrollment
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


@dataclass
class FaceTrack:
    """Track a face across multiple frames."""
    student_id: int
    student_name: str
    first_seen: datetime
    last_seen: datetime
    detection_count: int
    confidence_scores: List[float]
    cameras_seen: Set[str]
    marked_attendance: bool = False

    @property
    def average_confidence(self) -> float:
        return np.mean(self.confidence_scores) if self.confidence_scores else 0.0

    @property
    def duration_seconds(self) -> float:
        return (self.last_seen - self.first_seen).total_seconds()


class AttendanceService:
    def __init__(self):
        self.face_recognition = FaceRecognitionSystem()
        self.active_tracks: Dict[int, FaceTrack] = {}  # student_id -> FaceTrack
        self.processed_today: Set[int] = set()
        self.track_lock = threading.Lock()

        # Tracking thresholds
        self.min_detections = 3  # Minimum detections before marking attendance
        self.track_timeout = 300  # 5 minutes - remove track if not seen
        self.min_confidence = 0.7  # Minimum average confidence
        self.min_duration = 10  # Minimum seconds of tracking

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

        # Reset tracking for new session
        with self.track_lock:
            self.active_tracks.clear()

        # Load today's already marked attendance
        today = date.today()
        self.processed_today = set(
            a.student_id for a in db.query(Attendance).filter(
                Attendance.classroom_id == classroom_id,
                Attendance.check_in_time >= datetime.combine(today, time.min)
            ).all()
        )

        logger.info(f"Started attendance session for classroom {classroom_id} with {len(students)} students")

    def stop_attendance_session(self):
        """Stop attendance tracking and finalize any pending tracks."""
        with self.track_lock:
            # Log summary of tracking session
            total_tracks = len(self.active_tracks)
            marked_count = sum(1 for track in self.active_tracks.values() if track.marked_attendance)

            logger.info(f"Stopped attendance session. Total tracks: {total_tracks}, Marked: {marked_count}")

            self.active_tracks.clear()

    async def process_frame_with_tracking(
            self,
            frame: np.ndarray,
            classroom_id: int,
            db: Session,
            camera_key: str
    ) -> List[Dict]:
        """Process frame with face tracking across multiple detections."""
        # Detect and recognize faces
        _, results = self.face_recognition.process_frame(frame)

        current_time = datetime.now()
        marked_students = []

        with self.track_lock:
            # Update tracks with current detections
            detected_ids = set()

            for result in results:
                student_id = result.get('student_id')

                if not student_id or result['confidence'] < 0.6:
                    continue

                detected_ids.add(student_id)

                # Update or create track
                if student_id in self.active_tracks:
                    track = self.active_tracks[student_id]
                    track.last_seen = current_time
                    track.detection_count += 1
                    track.confidence_scores.append(result['confidence'])
                    track.cameras_seen.add(camera_key)
                else:
                    track = FaceTrack(
                        student_id=student_id,
                        student_name=result['name'],
                        first_seen=current_time,
                        last_seen=current_time,
                        detection_count=1,
                        confidence_scores=[result['confidence']],
                        cameras_seen={camera_key}
                    )
                    self.active_tracks[student_id] = track

                # Check if track meets criteria for marking attendance
                if (not track.marked_attendance and
                        student_id not in self.processed_today and
                        track.detection_count >= self.min_detections and
                        track.average_confidence >= self.min_confidence and
                        track.duration_seconds >= self.min_duration):

                    # Mark attendance
                    marked_student = self._mark_attendance(
                        student_id, classroom_id, track, db
                    )

                    if marked_student:
                        track.marked_attendance = True
                        self.processed_today.add(student_id)
                        marked_students.append(marked_student)

            # Clean up old tracks
            self._cleanup_old_tracks(current_time, detected_ids)

        return marked_students

    async def process_frame_direct(self, frame: np.ndarray, classroom_id: int, db: Session) -> List[Dict]:
        """Process a single frame without tracking (backward compatibility)."""
        return await self.process_frame_with_tracking(frame, classroom_id, db, "direct")

    def _mark_attendance(
            self,
            student_id: int,
            classroom_id: int,
            track: FaceTrack,
            db: Session
    ) -> Optional[Dict]:
        """Mark attendance for a student based on tracking data."""
        try:
            # Get classroom info
            classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
            if not classroom:
                return None

            # Determine attendance status
            now = datetime.now()
            class_start = datetime.combine(now.date(), classroom.start_time) if classroom.start_time else now
            late_threshold = class_start + timedelta(minutes=classroom.late_threshold_minutes)

            status = "present"
            if now > late_threshold:
                status = "late"

            # Calculate final confidence score
            confidence_score = track.average_confidence

            # Create attendance record
            attendance = Attendance(
                student_id=student_id,
                classroom_id=classroom_id,
                confidence_score=confidence_score,
                status=status,
                is_verified=confidence_score >= 0.85,
                verified_by=f"Auto-tracked ({track.detection_count} detections across {len(track.cameras_seen)} cameras)"
            )

            db.add(attendance)
            db.commit()

            # Get student info
            student = db.query(Student).filter(Student.id == student_id).first()

            logger.info(
                f"Marked attendance for {track.student_name} - {status} "
                f"(Confidence: {confidence_score:.2f}, Detections: {track.detection_count}, "
                f"Duration: {track.duration_seconds:.1f}s, Cameras: {len(track.cameras_seen)})"
            )

            return {
                'student_id': student.student_id,
                'student_name': student.full_name,
                'status': status,
                'confidence': confidence_score,
                'time': now.isoformat(),
                'detection_count': track.detection_count,
                'cameras': list(track.cameras_seen)
            }

        except Exception as e:
            logger.error(f"Error marking attendance: {e}")
            db.rollback()
            return None

    def _cleanup_old_tracks(self, current_time: datetime, detected_ids: Set[int]):
        """Remove tracks that haven't been seen recently."""
        tracks_to_remove = []

        for student_id, track in self.active_tracks.items():
            if student_id not in detected_ids:
                # Check if track has timed out
                if (current_time - track.last_seen).total_seconds() > self.track_timeout:
                    tracks_to_remove.append(student_id)

        for student_id in tracks_to_remove:
            removed_track = self.active_tracks.pop(student_id)
            logger.debug(
                f"Removed track for {removed_track.student_name} "
                f"(Last seen: {removed_track.last_seen}, Detections: {removed_track.detection_count})"
            )

    def get_active_tracks(self) -> List[Dict]:
        """Get current active face tracks."""
        with self.track_lock:
            return [
                {
                    'student_id': track.student_id,
                    'student_name': track.student_name,
                    'first_seen': track.first_seen.isoformat(),
                    'last_seen': track.last_seen.isoformat(),
                    'detection_count': track.detection_count,
                    'average_confidence': track.average_confidence,
                    'duration_seconds': track.duration_seconds,
                    'cameras': list(track.cameras_seen),
                    'marked': track.marked_attendance
                }
                for track in self.active_tracks.values()
            ]

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