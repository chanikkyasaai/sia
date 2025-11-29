import datetime
from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, Numeric
from app.db.session import Base

class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    quantity_on_hand = Column(Numeric, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))