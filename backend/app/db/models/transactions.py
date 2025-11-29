from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.session import Base

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    type = Column(String, nullable=False)
    amount = Column(Numeric, nullable=False)
    quantity = Column(Numeric, nullable=True)
    note = Column(String, nullable=True)
    source = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now(timezone.utc))

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")