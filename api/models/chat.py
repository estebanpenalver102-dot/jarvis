from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base
import uuid

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), nullable=False,
                         default=uuid.UUID("00000000-0000-0000-0000-000000000001"))
    title       = Column(Text)
    mode        = Column(String(20), default="text")
    metadata_   = Column("metadata", JSONB, default={})
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
                        nullable=False)
    role       = Column(String(20), nullable=False)
    content    = Column(Text, nullable=False)
    tool_calls = Column(JSONB)
    metadata_  = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
