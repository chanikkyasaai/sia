import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, JSON, Text
from app.db.session import Base

class EditLog(Base):
    __tablename__ = 'edit_logs'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))