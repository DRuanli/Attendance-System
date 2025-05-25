# app/api/routes/scheduler.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from app.api.dependencies import get_db
from app.core.background_service import background_service
from app.models import Classroom
from pydantic import BaseModel
from config import settings

router = APIRouter(tags=["scheduler"])


class ManualSessionRequest(BaseModel):
    classroom_id: int
    duration_minutes: int = 120


class CameraConfigRequest(BaseModel):
    classroom_id: int
    cameras: List[Dict]


@router.get("/status")
async def get_scheduler_status():
    """Get current status of the automatic attendance scheduler."""
    if not settings.enable_background_service:
        raise HTTPException(status_code=503, detail="Background service is disabled")

    return background_service.get_status()


@router.get("/sessions/active")
async def get_active_sessions():
    """Get all active attendance sessions."""
    if not settings.enable_background_service:
        raise HTTPException(status_code=503, detail="Background service is disabled")

    status = background_service.get_status()
    return status["scheduler"]["active_sessions"]


@router.post("/sessions/manual")
async def start_manual_session(request: ManualSessionRequest, db: Session = Depends(get_db)):
    """Start a manual attendance session outside of regular schedule."""
    # Verify classroom exists
    classroom = db.query(Classroom).filter(Classroom.id == request.classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    if not settings.enable_background_service:
        raise HTTPException(status_code=503, detail="Background service is disabled")

    # Add manual session
    background_service.scheduler_service.add_manual_session(
        request.classroom_id,
        request.duration_minutes
    )

    return {
        "status": "success",
        "message": f"Manual session started for classroom {classroom.course_name}",
        "duration_minutes": request.duration_minutes,
        "end_time": datetime.now().isoformat()
    }


@router.delete("/sessions/{classroom_id}")
async def stop_session(classroom_id: int):
    """Stop an active attendance session."""
    if not settings.enable_background_service:
        raise HTTPException(status_code=503, detail="Background service is disabled")

    # Check if session exists
    active_sessions = background_service.scheduler_service.get_active_sessions()
    if classroom_id not in active_sessions:
        raise HTTPException(status_code=404, detail="No active session for this classroom")

    # Stop the session
    await background_service.scheduler_service._stop_attendance_session(classroom_id)

    return {"status": "success", "message": "Session stopped"}


@router.get("/schedules")
async def get_all_schedules():
    """Get all scheduled attendance sessions."""
    if not settings.enable_background_service:
        raise HTTPException(status_code=503, detail="Background service is disabled")

    jobs = background_service.scheduler_service.scheduler.get_jobs()

    schedules = []
    for job in jobs:
        if job.id.startswith("start_classroom_"):
            classroom_id = int(job.id.replace("start_classroom_", ""))
            schedules.append({
                "classroom_id": classroom_id,
                "job_id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

    return schedules


@router.get("/tracks/active")
async def get_active_face_tracks():
    """Get currently active face tracks from attendance service."""
    if not settings.enable_background_service:
        raise HTTPException(status_code=503, detail="Background service is disabled")

    # Get tracks from all active sessions
    all_tracks = []
    active_sessions = background_service.scheduler_service.active_sessions

    for classroom_id in active_sessions:
        tracks = background_service.scheduler_service.attendance_service.get_active_tracks()
        for track in tracks:
            track["classroom_id"] = classroom_id
            all_tracks.append(track)

    return all_tracks


@router.post("/cameras/config")
async def update_camera_config(request: CameraConfigRequest):
    """Update camera configuration for a classroom."""
    if not settings.enable_background_service:
        raise HTTPException(status_code=503, detail="Background service is disabled")

    # Update configuration
    from app.core.camera_handler import CameraConfig, CameraType

    configs = []
    for cam in request.cameras:
        config = CameraConfig(
            camera_id=cam["camera_id"],
            camera_type=CameraType(cam["camera_type"]),
            name=cam["name"],
            location=cam["location"],
            username=cam.get("username"),
            password=cam.get("password"),
            fps=cam.get("fps", 10),
            resolution=tuple(cam.get("resolution", [640, 480]))
        )
        configs.append(config)

    # Update in scheduler service
    background_service.scheduler_service.camera_configs[request.classroom_id] = configs

    # Save to file
    import json
    try:
        with open(settings.camera_config_file, 'r') as f:
            all_configs = json.load(f)
    except:
        all_configs = {}

    all_configs[str(request.classroom_id)] = [
        {
            "camera_id": c.camera_id,
            "camera_type": c.camera_type.value,
            "name": c.name,
            "location": c.location,
            "username": c.username,
            "password": c.password,
            "fps": c.fps,
            "resolution": list(c.resolution)
        }
        for c in configs
    ]

    with open(settings.camera_config_file, 'w') as f:
        json.dump(all_configs, f, indent=2)

    return {
        "status": "success",
        "message": f"Updated camera configuration for classroom {request.classroom_id}",
        "cameras": len(configs)
    }


@router.get("/cameras/test/{classroom_id}")
async def test_cameras(classroom_id: int):
    """Test camera connections for a classroom."""
    if not settings.enable_background_service:
        raise HTTPException(status_code=503, detail="Background service is disabled")

    # Get camera configs
    configs = background_service.scheduler_service.camera_configs.get(classroom_id, [])
    if not configs:
        raise HTTPException(status_code=404, detail="No cameras configured for this classroom")

    # Test each camera
    results = []
    for config in configs:
        from app.core.camera_handler import CameraStream
        camera = CameraStream(config)

        success = camera._initialize_capture()
        if success:
            camera.stop()

        results.append({
            "camera_id": config.camera_id,
            "name": config.name,
            "type": config.camera_type.value,
            "location": config.location,
            "connected": success
        })

    return {
        "classroom_id": classroom_id,
        "tested_at": datetime.now().isoformat(),
        "cameras": results
    }