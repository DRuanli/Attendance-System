# app/api/dependencies.py
from typing import Generator
from config.database import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()