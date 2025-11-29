from pydantic import BaseModel
from typing import Optional

class ReminderBase(BaseModel):
    amount: float
    due_date: str
    channel: str
    message: Optional[str]
    status: str
    sent_at: Optional[str]
    last_error: Optional[str]

class ReminderCreate(ReminderBase):
    business_id: int
    customer_id: int

class ReminderUpdate(ReminderBase):
    pass

class ReminderResponse(ReminderBase):
    id: int

    class Config:
        from_attributes = True