# scripts/setup_database.py
# !/usr/bin/env python
"""
Database setup script
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.models import Base
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """Create all database tables."""
    engine = create_engine(settings.database_url)

    logger.info("Creating database tables...")
    Base.metadata.create_all(engine)
    logger.info("Database setup complete!")


if __name__ == "__main__":
    setup_database()