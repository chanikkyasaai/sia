from pydantic import BaseModel
from typing import Optional

class ConversationLogBase(BaseModel):
    raw_text: Optional[str]
    transcript_language: Optional[str]
    parse_confidence: Optional[float]
    parsed_payload: Optional[dict]
    audio_url: Optional[str]

class ConversationLogCreate(ConversationLogBase):
    business_id: int
    user_id: Optional[int]
    linked_transaction_id: Optional[int]

class ConversationLogUpdate(ConversationLogBase):
    pass

class ConversationLogResponse(ConversationLogBase):
    id: int
    business_id: int
    user_id: Optional[int]
    linked_transaction_id: Optional[int]

    class Config:
        from_attributes = True