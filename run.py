# run.py
# !/usr/bin/env python
"""
Startup script for Classroom Attendance System
"""
import uvicorn
import sys
import os
from app.utils.helpers import create_directories


def main():
    # Create necessary directories
    create_directories()

    # Check Python version
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required")
        sys.exit(1)

    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()