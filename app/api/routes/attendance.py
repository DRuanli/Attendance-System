# app/api/routes/attendance.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, time
import numpy as np
import cv2
import io
from app.api.dependencies import get_db
from app.models import Attendance, Student, Classroom, Enrollment
from app.services.attendance_service import AttendanceService
from config import settings

router = APIRouter(tags=["attendance"])
attendance_service = AttendanceService()


@router.post("/session/start/{classroom_id}")
async def start_attendance_session(
        classroom_id: int,
        db: Session = Depends(get_db)
):
    """Start an attendance session for face recognition."""
    # Verify classroom exists
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    try:
        attendance_service.start_attendance_session(classroom_id, db)
        return {
            "status": "success",
            "message": "Attendance session started",
            "classroom": classroom.course_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/stop")
async def stop_attendance_session():
    """Stop the current attendance session."""
    attendance_service.stop_attendance_session()
    return {"status": "success", "message": "Attendance session stopped"}


@router.post("/mark")
async def mark_attendance_manual(
        student_id: str = Form(...),
        classroom_id: int = Form(...),
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
        classroom_id: int = Form(...),
        image: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """Process uploaded image frame for attendance recognition."""
    # Verify classroom
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # Read and decode image
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

    # Process the frame
    try:
        # Ensure attendance session is started
        if not hasattr(attendance_service, 'face_recognition') or \
                len(attendance_service.face_recognition.known_face_encodings) == 0:
            attendance_service.start_attendance_session(classroom_id, db)

        # Process the frame directly
        marked_students = await attendance_service.process_frame_direct(frame, classroom_id, db)

        return {
            "status": "success",
            "recognized_count": len(marked_students),
            "students": marked_students
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in face recognition: {str(e)}")


@router.post("/verify-face")
async def verify_student_face(
        student_id: str = Form(...),
        image: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """Verify if the uploaded face matches the student."""
    # Get student
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not student.face_encoding:
        raise HTTPException(status_code=400, detail="Student has no face encoding")

    # Read and decode image
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        image_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image_array is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

    # Verify face
    try:
        # Detect faces in the image
        aligned_faces, _ = attendance_service.face_recognition.detector.detect_and_align_faces(image_array)

        if not aligned_faces:
            return {"verified": False, "message": "No face detected", "confidence": 0.0}

        # Use the first face for verification
        is_match, confidence = attendance_service.face_recognition.verify_face(
            aligned_faces[0],
            student.id
        )

        return {
            "verified": is_match,
            "confidence": float(confidence),
            "message": "Face verified" if is_match else "Face does not match"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in face verification: {str(e)}")


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


@router.get("/classroom/{classroom_id}/absentees")
def get_absentees(classroom_id: int, db: Session = Depends(get_db)):
    """Get list of absent students for today."""
    absentees = attendance_service.get_absentees(classroom_id, db)
    return {
        "classroom_id": classroom_id,
        "date": date.today(),
        "absentees": absentees,
        "count": len(absentees)
    }