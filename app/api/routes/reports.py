# app/api/routes/reports.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import pandas as pd
import io
from app.api.dependencies import get_db
from app.models import Attendance, Student, Classroom, Enrollment
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])
report_service = ReportService()


@router.get("/classroom/{classroom_id}/attendance-report")
def generate_classroom_attendance_report(
        classroom_id: int,
        start_date: date,
        end_date: date,
        format: str = "csv",
        db: Session = Depends(get_db)
):
    """Generate attendance report for a classroom."""
    # Verify classroom
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # Get attendance data
    report_data = report_service.generate_attendance_report(
        classroom_id=classroom_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )

    if format == "csv":
        # Convert to CSV
        df = pd.DataFrame(report_data)
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        stream.seek(0)

        return StreamingResponse(
            io.BytesIO(stream.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=attendance_report_{classroom_id}_{start_date}_{end_date}.csv"
            }
        )
    else:
        return report_data


@router.get("/statistics/classroom/{classroom_id}")
def get_classroom_statistics(
        classroom_id: int,
        db: Session = Depends(get_db)
):
    """Get attendance statistics for a classroom."""
    # Get enrollments
    total_students = db.query(Enrollment).filter(
        Enrollment.classroom_id == classroom_id
    ).count()

    # Get attendance stats for last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)

    attendance_count = db.query(Attendance).filter(
        Attendance.classroom_id == classroom_id,
        Attendance.check_in_time >= thirty_days_ago
    ).count()

    late_count = db.query(Attendance).filter(
        Attendance.classroom_id == classroom_id,
        Attendance.check_in_time >= thirty_days_ago,
        Attendance.status == "late"
    ).count()

    return {
        "total_students": total_students,
        "total_attendance_last_30_days": attendance_count,
        "late_arrivals_last_30_days": late_count,
        "average_attendance_rate": (attendance_count / (total_students * 30)) * 100 if total_students > 0 else 0
    }
