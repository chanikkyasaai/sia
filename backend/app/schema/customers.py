from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class CustomerBase(BaseModel):
    name: str
    phone: str
    info: Optional[str]
    risk_level: str
    credit: Optional[int]
    avg_delay_days: Optional[int]

class CustomerCreate(CustomerBase):
    business_id: int

class CustomerUpdate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True