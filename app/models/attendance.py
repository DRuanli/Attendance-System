# app/models/attendance.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)

    # Attendance details
    check_in_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    check_out_time = Column(DateTime(timezone=True))
    confidence_score = Column(Float)  # Face recognition confidence
    status = Column(String(20), default="present")  # present, late, excused, absent

    # Verification
    is_verified = Column(Boolean, default=True)  # False if manual override needed
    verified_by = Column(String(100))  # Teacher name if manually verified

    # Meta
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("Student", back_populates="attendances")
    classroom = relationship("Classroom", back_populates="attendances")