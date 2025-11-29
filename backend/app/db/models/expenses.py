from sqlalchemy import Column, Integer, Numeric, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base


class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey(
        'businesses.id'), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    # PURCHASE, OPERATING, FUEL, TRANSPORT, MISC
    type = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
    # when the expense happened (local time)
    occurred_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now(timezone.utc))
    source = Column(String(20), nullable=False,
                    default='MANUAL')  # VOICE, MANUAL, IMPORT

    # Relationship
    business = relationship("Business", back_populates="expenses")
