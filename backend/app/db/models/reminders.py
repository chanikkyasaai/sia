from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Numeric, Date
from app.db.session import Base

class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    amount = Column(Numeric, nullable=False)
    due_date = Column(Date, nullable=False)
    channel = Column(String, nullable=False)
    message = Column(String, nullable=True)
    status = Column(String, nullable=False)
    sent_at = Column(TIMESTAMP, nullable=True)
    last_error = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now(timezone.utc))