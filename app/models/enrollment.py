# app/models/enrollment.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    classroom = relationship("Classroom", back_populates="enrollments")

    # Ensure unique enrollment
    __table_args__ = (
        UniqueConstraint('student_id', 'classroom_id', name='unique_enrollment'),
    )
