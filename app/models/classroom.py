# app/models/classroom.py
from sqlalchemy import Column, Integer, String, DateTime, Time, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, nullable=False)
    course_name = Column(String(200), nullable=False)
    instructor_name = Column(String(100))
    room_number = Column(String(20))

    # Schedule
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_time = Column(Time)
    end_time = Column(Time)
    semester = Column(String(20))

    # Settings
    late_threshold_minutes = Column(Integer, default=15)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    attendances = relationship("Attendance", back_populates="classroom")
    enrollments = relationship("Enrollment", back_populates="classroom")