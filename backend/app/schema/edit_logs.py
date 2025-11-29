from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class EditLogBase(BaseModel):
    entity_type: str
    entity_id: int
    before: Optional[dict]
    after: Optional[dict]
    reason: Optional[str]

class EditLogCreate(EditLogBase):
    business_id: int
    user_id: Optional[int]

class EditLogUpdate(EditLogBase):
    pass

class EditLogResponse(EditLogBase):
    id: int
    business_id: int
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True