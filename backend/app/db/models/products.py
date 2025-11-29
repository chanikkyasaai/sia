from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.session import Base

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    low_stock_threshold = Column(Numeric, nullable=True)
    avg_cost_price = Column(Numeric, nullable=True)
    avg_sale_price = Column(Numeric, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now(timezone.utc))

    # Add the transactions relationship
    transactions = relationship("Transaction", back_populates="product")