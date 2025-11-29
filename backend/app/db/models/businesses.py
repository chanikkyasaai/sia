from datetime import datetime,timezone
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Business(Base):
    __tablename__ = 'businesses'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    location = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now(timezone.utc))

    # Add the relationship to DailyAnalytics
    daily_analytics = relationship("DailyAnalytics", back_populates="business", cascade="all, delete-orphan")

    # Add the relationship to Expenses
    expenses = relationship("Expense", back_populates="business", cascade="all, delete-orphan")