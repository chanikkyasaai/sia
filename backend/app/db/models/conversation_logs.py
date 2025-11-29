import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, JSON, Numeric
from app.db.session import Base

class ConversationLog(Base):
    __tablename__ = 'conversation_logs'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    raw_text = Column(String, nullable=True)
    transcript_language = Column(String, nullable=True)
    parse_confidence = Column(Numeric, nullable=True)
    parsed_payload = Column(JSON, nullable=True)
    audio_url = Column(String, nullable=True)
    linked_transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))