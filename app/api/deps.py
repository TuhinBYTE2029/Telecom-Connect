"""FastAPI dependency providers."""
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

# Re-export get_db for cleaner imports in routers
__all__ = ["get_db"]
