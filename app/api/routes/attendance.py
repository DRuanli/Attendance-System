# app/api/routes/attendance.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, time
from app.api.dependencies import get_db
from app.models import Attendance, Student, Classroom
from app.services.attendance_service import AttendanceService
from config import settings

router = APIRouter(tags=["attendance"])
attendance_service = AttendanceService()


@router.post("/mark")
async def mark_attendance_manual(
        student_id: str,
        classroom_id: int,
        db: Session = Depends(get_db)
):
    """Manually mark attendance for a student."""
    # Verify student exists
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Verify classroom exists
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # Check if already marked today
    today = date.today()
    existing = db.query(Attendance).filter(
        Attendance.student_id == student.id,
        Attendance.classroom_id == classroom_id,
        Attendance.check_in_time >= datetime.combine(today, time.min),
        Attendance.check_in_time <= datetime.combine(today, time.max)
    ).first()

    if existing:
        return {"message": "Attendance already marked", "attendance_id": existing.id}

    # Mark attendance
    attendance = Attendance(
        student_id=student.id,
        classroom_id=classroom_id,
        confidence_score=1.0,
        is_verified=True,
        verified_by="Manual Entry"
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return {
        "message": "Attendance marked successfully",
        "attendance_id": attendance.id,
        "student_name": student.full_name,
        "check_in_time": attendance.check_in_time
    }


@router.post("/process-frame")
async def process_camera_frame(
        classroom_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """Process current camera frame for attendance."""
    # Verify classroom
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # Process frame in background
    background_tasks.add_task(
        attendance_service.process_attendance_frame,
        classroom_id=classroom_id,
        db=db
    )

    return {"message": "Processing frame for attendance"}


@router.get("/classroom/{classroom_id}/today")
def get_today_attendance(classroom_id: int, db: Session = Depends(get_db)):
    """Get today's attendance for a classroom."""
    today = date.today()

    attendances = db.query(Attendance).join(Student).filter(
        Attendance.classroom_id == classroom_id,
        Attendance.check_in_time >= datetime.combine(today, time.min),
        Attendance.check_in_time <= datetime.combine(today, time.max)
    ).all()

    return [
        {
            "id": a.id,
            "student_id": a.student.student_id,
            "student_name": a.student.full_name,
            "check_in_time": a.check_in_time,
            "status": a.status,
            "confidence_score": a.confidence_score,
            "is_verified": a.is_verified
        }
        for a in attendances
    ]


@router.get("/student/{student_id}/history")
def get_student_attendance_history(
        student_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        db: Session = Depends(get_db)
):
    """Get attendance history for a student."""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    query = db.query(Attendance).filter(Attendance.student_id == student.id)

    if start_date:
        query = query.filter(Attendance.check_in_time >= datetime.combine(start_date, time.min))
    if end_date:
        query = query.filter(Attendance.check_in_time <= datetime.combine(end_date, time.max))

    attendances = query.order_by(Attendance.check_in_time.desc()).all()

    return [
        {
            "date": a.check_in_time.date(),
            "classroom": a.classroom.course_name,
            "check_in_time": a.check_in_time,
            "status": a.status,
            "confidence_score": a.confidence_score
        }
        for a in attendances
    ]