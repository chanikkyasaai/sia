import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    info = Column(String, nullable=True)
    risk_level = Column(String, nullable=False)
    avg_delay_days = Column(Integer, nullable=True)
    credit = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))

    # Add the transactions relationship
    transactions = relationship("Transaction", back_populates="customer")
