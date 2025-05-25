# app/api/routes/students.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime
from app.api.dependencies import get_db
from app.models import Student
from app.services.student_service import StudentService
from app.utils.validators import validate_image_file
from config import settings

router = APIRouter(tags=["students"])
student_service = StudentService()


@router.post("/register")
async def register_student(
        student_id: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: str = Form(...),
        phone: Optional[str] = Form(""),
        photos: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
):
    """Register a new student with photos for face recognition."""
    # Validate at least 3 photos
    if len(photos) < 3:
        raise HTTPException(status_code=400, detail="At least 3 photos required")

    # Check if student already exists
    existing = db.query(Student).filter(
        (Student.student_id == student_id) | (Student.email == email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")

    # Validate and save photos
    photo_paths = []
    student_dir = os.path.join(settings.upload_dir, student_id)
    os.makedirs(student_dir, exist_ok=True)

    for photo in photos:
        # Validate file
        if not validate_image_file(photo):
            raise HTTPException(status_code=400, detail=f"Invalid image file: {photo.filename}")

        # Save photo
        filename = f"{uuid.uuid4()}{os.path.splitext(photo.filename)[1]}"
        filepath = os.path.join(student_dir, filename)

        content = await photo.read()
        with open(filepath, "wb") as f:
            f.write(content)

        photo_paths.append(filepath)

    # Generate face encoding
    try:
        encoding = await student_service.generate_student_encoding(photo_paths)
        if encoding is None:
            raise HTTPException(status_code=400, detail="No face detected in photos")
    except Exception as e:
        # Clean up uploaded files
        for path in photo_paths:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(status_code=400, detail=str(e))

    # Create student
    student = Student(
        student_id=student_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        face_encoding=encoding,
        photos_count=len(photos)
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return {
        "message": "Student registered successfully",
        "student_id": student.id,
        "full_name": student.full_name
    }


@router.get("/", response_model=List[dict])
def get_all_students(
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        db: Session = Depends(get_db)
):
    """Get all students with pagination."""
    query = db.query(Student)

    if is_active is not None:
        query = query.filter(Student.is_active == is_active)

    students = query.offset(skip).limit(limit).all()

    return [
        {
            "id": s.id,
            "student_id": s.student_id,
            "full_name": s.full_name,
            "email": s.email,
            "is_active": s.is_active,
            "created_at": s.created_at
        }
        for s in students
    ]


@router.get("/{student_id}")
def get_student(student_id: str, db: Session = Depends(get_db)):
    """Get student by ID."""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "id": student.id,
        "student_id": student.student_id,
        "full_name": student.full_name,
        "email": student.email,
        "phone": student.phone,
        "is_active": student.is_active,
        "photos_count": student.photos_count,
        "created_at": student.created_at
    }


@router.put("/{student_id}/deactivate")
def deactivate_student(student_id: str, db: Session = Depends(get_db)):
    """Deactivate a student."""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_active = False
    db.commit()

    return {"message": "Student deactivated successfully"}
