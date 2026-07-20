"""SQLAlchemy ORM models. See Phase 5 database design for full schema rationale."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    privacy_policy = Column(String(50), nullable=False, default="strict")
    created_at = Column(DateTime, default=datetime.utcnow)

    api_keys = relationship("ApiKey", back_populates="organization", cascade="all,delete")
    traces = relationship("RoutingTrace", back_populates="organization", cascade="all,delete")
    budget = relationship("Budget", back_populates="organization", uselist=False, cascade="all,delete")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    label = Column(String(255), default="")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="api_keys")


class Backend(Base):
    __tablename__ = "backends"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(100), unique=True, nullable=False)
    provider = Column(String(50), nullable=False)
    context_window = Column(Integer, nullable=False)
    cost_per_1k_input = Column(Numeric(10, 6), nullable=False)
    cost_per_1k_output = Column(Numeric(10, 6), nullable=False)
    is_local = Column(Boolean, default=False)
    active = Column(Boolean, default=True)


class RoutingTrace(Base):
    __tablename__ = "routing_traces"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=True)
    backend_name = Column(String(100))
    intent = Column(String(50))
    complexity_score = Column(Float)
    risk_level = Column(String(20))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost = Column(Numeric(10, 6))
    latency_ms = Column(Integer)
    cache_hit = Column(Boolean, default=False)
    reason = Column(Text)
    candidate_scores = Column(Text)  # JSON-encoded dict, kept simple for SQLite portability
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="traces")
    feedback = relationship("Feedback", back_populates="trace", uselist=False, cascade="all,delete")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=gen_uuid)
    trace_id = Column(String, ForeignKey("routing_traces.id"), nullable=False)
    rating = Column(String(10), nullable=False)  # 'up' | 'down'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    trace = relationship("RoutingTrace", back_populates="feedback")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), unique=True, nullable=False)
    monthly_limit = Column(Numeric(10, 2), nullable=False, default=100.0)
    current_spend = Column(Numeric(10, 2), nullable=False, default=0.0)

    organization = relationship("Organization", back_populates="budget")
