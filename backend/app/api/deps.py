from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

# Dependency to get the current database session

def get_db_session():
    return next(get_db())