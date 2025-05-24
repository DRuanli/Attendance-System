# scripts/populate_demo_data.py
# !/usr/bin/env python
"""
Populate database with demo data for testing
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models import Student, Classroom, Enrollment
from config.database import SessionLocal, engine
from datetime import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def populate_demo_data():
    """Add demo data to database."""
    db = SessionLocal()

    try:
        # Create demo classroom
        classroom = Classroom(
            course_code="CS101",
            course_name="Introduction to Computer Science",
            instructor_name="Dr. Smith",
            room_number="A201",
            day_of_week=1,  # Monday
            start_time=time(9, 0),
            end_time=time(10, 30),
            semester="Fall 2024"
        )
        db.add(classroom)
        db.commit()

        logger.info(f"Created classroom: {classroom.course_name}")

        # Create demo students
        demo_students = [
            {"student_id": "STU001", "first_name": "John", "last_name": "Doe", "email": "john.doe@example.com"},
            {"student_id": "STU002", "first_name": "Jane", "last_name": "Smith", "email": "jane.smith@example.com"},
            {"student_id": "STU003", "first_name": "Bob", "last_name": "Johnson", "email": "bob.johnson@example.com"},
        ]

        for student_data in demo_students:
            student = Student(**student_data)
            db.add(student)
            db.commit()

            # Enroll in classroom
            enrollment = Enrollment(student_id=student.id, classroom_id=classroom.id)
            db.add(enrollment)
            db.commit()

            logger.info(f"Created student: {student.full_name}")

        logger.info("Demo data populated successfully!")

    except Exception as e:
        logger.error(f"Error populating demo data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    populate_demo_data()