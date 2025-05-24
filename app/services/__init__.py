# app/services/__init__.py
from .student_service import StudentService
from .attendance_service import AttendanceService
from .report_service import ReportService

__all__ = ["StudentService", "AttendanceService", "ReportService"]