# scripts/init_database.py
# !/usr/bin/env python
"""
Initialize database with required data
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models import Student, Classroom, Enrollment
from config.database import SessionLocal, engine, Base
from datetime import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with essential data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if classroom exists
        existing_classroom = db.query(Classroom).filter(Classroom.id == 1).first()
        if not existing_classroom:
            # Create default classroom
            classroom = Classroom(
                id=1,
                course_code="CS101",
                course_name="Introduction to Computer Science",
                instructor_name="Dr. Smith",
                room_number="A201",
                day_of_week=1,  # Monday
                start_time=time(9, 0),
                end_time=time(10, 30),
                semester="Fall 2024",
                late_threshold_minutes=15
            )
            db.add(classroom)
            db.commit()
            logger.info(f"Created default classroom: {classroom.course_name}")
        else:
            logger.info("Default classroom already exists")

        # Create demo students if none exist
        existing_students = db.query(Student).count()
        if existing_students == 0:
            demo_students = [
                {"student_id": "STU001", "first_name": "John", "last_name": "Doe", "email": "john.doe@example.com"},
                {"student_id": "STU002", "first_name": "Jane", "last_name": "Smith", "email": "jane.smith@example.com"},
                {"student_id": "STU003", "first_name": "Bob", "last_name": "Johnson",
                 "email": "bob.johnson@example.com"},
            ]

            for student_data in demo_students:
                student = Student(**student_data)
                db.add(student)
                db.commit()

                # Enroll in default classroom
                enrollment = Enrollment(student_id=student.id, classroom_id=1)
                db.add(enrollment)
                db.commit()

                logger.info(f"Created demo student: {student.full_name}")

        logger.info("Database initialization complete!")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()