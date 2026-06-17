from sqlalchemy import Column, String, Text, Float, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base
import uuid

class Memory(Base):
    __tablename__ = "memories"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), nullable=False,
                        default=uuid.UUID("00000000-0000-0000-0000-000000000001"))
    content    = Column(Text, nullable=False)
    summary    = Column(Text)
    embedding  = Column(Vector(1536))
    category   = Column(String(50), default="episodic")
    metadata_  = Column("metadata", JSONB, default={})
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type     = Column(String(50), nullable=False)
    goal           = Column(Text, nullable=False)
    plan           = Column(JSONB, default=[])
    status         = Column(String(20), default="pending")
    result_summary = Column(Text)
    error_message  = Column(Text)
    context_refs   = Column(ARRAY(UUID(as_uuid=True)), default=[])
    metadata_      = Column("metadata", JSONB, default={})
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at   = Column(DateTime(timezone=True))
