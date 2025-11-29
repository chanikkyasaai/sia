from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, TIMESTAMP
from app.db.session import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    locale = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now(timezone.utc))
