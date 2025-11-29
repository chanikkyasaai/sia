from pydantic import BaseModel
from typing import Optional

class BusinessBase(BaseModel):
    name: str
    phone: str
    location: Optional[str]
    domain: Optional[str]

class BusinessCreate(BusinessBase):
    user_id: int

class BusinessUpdate(BusinessBase):
    pass

class BusinessResponse(BusinessBase):
    id: int

    class Config:
        from_attributes = True