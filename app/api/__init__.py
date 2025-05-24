# app/api/__init__.py
from . import routes
from .dependencies import get_db

__all__ = ["routes", "get_db"]