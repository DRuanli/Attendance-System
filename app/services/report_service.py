# app/services/report_service.py
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Dict
from app.models import Student, Attendance, Classroom, Enrollment
import pandas as pd


class ReportService:

    def generate_attendance_report(
            self,
            classroom_id: int,
            start_date: date,
            end_date: date,
            db: Session
    ) -> List[Dict]:
        """Generate detailed attendance report for a classroom."""
        # Get all enrolled students
        enrollments = db.query(Enrollment).filter(
            Enrollment.classroom_id == classroom_id
        ).all()

        report_data = []

        for enrollment in enrollments:
            student = enrollment.student

            # Get attendance records
            attendances = db.query(Attendance).filter(
                Attendance.student_id == student.id,
                Attendance.classroom_id == classroom_id,
                Attendance.check_in_time >= datetime.combine(start_date, time.min),
                Attendance.check_in_time <= datetime.combine(end_date, time.max)
            ).all()

            # Calculate statistics
            total_classes = (end_date - start_date).days + 1
            present_count = len([a for a in attendances if a.status == "present"])
            late_count = len([a for a in attendances if a.status == "late"])
            absent_count = total_classes - len(attendances)

            attendance_rate = (len(attendances) / total_classes * 100) if total_classes > 0 else 0

            report_data.append({
                'student_id': student.student_id,
                'student_name': student.full_name,
                'email': student.email,
                'total_classes': total_classes,
                'present': present_count,
                'late': late_count,
                'absent': absent_count,
                'attendance_rate': round(attendance_rate, 2),
                'last_attendance': max([a.check_in_time for a in attendances]) if attendances else None
            })

        return report_data

    def generate_student_report(
            self,
            student_id: int,
            semester: str,
            db: Session
    ) -> Dict:
        """Generate attendance report for a specific student."""
        # Get student
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {}

        # Get all enrollments for the semester
        enrollments = db.query(Enrollment).join(Classroom).filter(
            Enrollment.student_id == student_id,
            Classroom.semester == semester
        ).all()

        courses_data = []

        for enrollment in enrollments:
            classroom = enrollment.classroom

            # Get attendance for this course
            attendances = db.query(Attendance).filter(
                Attendance.student_id == student_id,
                Attendance.classroom_id == classroom.id
            ).all()

            present = len([a for a in attendances if a.status == "present"])
            late = len([a for a in attendances if a.status == "late"])

            courses_data.append({
                'course_code': classroom.course_code,
                'course_name': classroom.course_name,
                'instructor': classroom.instructor_name,
                'total_attended': len(attendances),
                'present': present,
                'late': late,
                'attendance_rate': round((len(attendances) / 30 * 100), 2)  # Assuming 30 classes
            })

        return {
            'student': {
                'id': student.student_id,
                'name': student.full_name,
                'email': student.email
            },
            'semester': semester,
            'courses': courses_data,
            'overall_attendance_rate': round(
                sum(c['attendance_rate'] for c in courses_data) / len(courses_data), 2
            ) if courses_data else 0
        }

    def get_daily_summary(self, classroom_id: int, date: date, db: Session) -> Dict:
        """Get attendance summary for a specific day."""
        start_time = datetime.combine(date, time.min)
        end_time = datetime.combine(date, time.max)

        # Get attendance records
        attendances = db.query(Attendance).filter(
            Attendance.classroom_id == classroom_id,
            Attendance.check_in_time >= start_time,
            Attendance.check_in_time <= end_time
        ).all()

        # Get total enrolled
        total_enrolled = db.query(Enrollment).filter(
            Enrollment.classroom_id == classroom_id
        ).count()

        present = len([a for a in attendances if a.status == "present"])
        late = len([a for a in attendances if a.status == "late"])
        absent = total_enrolled - len(attendances)

        return {
            'date': date,
            'total_enrolled': total_enrolled,
            'present': present,
            'late': late,
            'absent': absent,
            'attendance_rate': round((len(attendances) / total_enrolled * 100), 2) if total_enrolled > 0 else 0
        }