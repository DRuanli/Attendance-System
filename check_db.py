#!/usr/bin/env python
# check_db.py - Check database contents

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from app.models import Classroom, Student, Enrollment


def check_database():
    """Check database contents."""
    db = SessionLocal()

    try:
        # Check classrooms
        classrooms = db.query(Classroom).all()
        print(f"📚 Classrooms in database: {len(classrooms)}")
        for classroom in classrooms:
            print(f"  - ID: {classroom.id}, Code: {classroom.course_code}, Name: {classroom.course_name}")

        # Check students
        students = db.query(Student).all()
        print(f"\n👥 Students in database: {len(students)}")
        for student in students:
            print(f"  - ID: {student.student_id}, Name: {student.full_name}")

        # Check enrollments
        enrollments = db.query(Enrollment).all()
        print(f"\n📋 Enrollments in database: {len(enrollments)}")

        if len(classrooms) == 0:
            print("\n⚠️  No classrooms found! Run: python scripts/init_database.py")

    finally:
        db.close()


if __name__ == "__main__":
    check_database()