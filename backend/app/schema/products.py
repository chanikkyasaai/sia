from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    name: str
    unit: str
    low_stock_threshold: Optional[float]
    avg_cost_price: Optional[float]
    avg_sale_price: Optional[float]
    is_active: bool

class ProductCreate(ProductBase):
    business_id: int

class ProductUpdate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    business_id: int
    created_at: datetime

    class Config:
        from_attributes = True