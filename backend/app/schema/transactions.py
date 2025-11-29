from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.schema.customers import CustomerResponse
from app.schema.products import ProductResponse

class TransactionBase(BaseModel):
    type: str
    amount: float
    quantity: Optional[float]
    note: Optional[str]
    source: str
    

class TransactionCreate(TransactionBase):
    business_id: int
    customer_id: Optional[int]
    product_id: Optional[int]

class TransactionUpdate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime
    customer: Optional[CustomerResponse]
    product: Optional[ProductResponse]

    class Config:
        from_attributes = True