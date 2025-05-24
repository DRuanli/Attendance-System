# app/models/student.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20))

    # Face recognition data
    face_encoding = Column(LargeBinary)  # Stored as binary pickle
    photos_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    attendances = relationship("Attendance", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="student")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"