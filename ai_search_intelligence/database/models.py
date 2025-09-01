"""Database models for AI Search Intelligence System."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean,
    JSON, ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Query(Base, TimestampMixin):
    """Queries being tracked across search engines."""
    __tablename__ = "queries"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    query_text = Column(String(500), nullable=False)
    category = Column(String(100))
    priority = Column(String(20), default="medium")  # low, medium, high
    is_active = Column(Boolean, default=True)
    collection_interval = Column(Integer, default=3600)  # seconds
    
    # Relationships
    citations = relationship("Citation", back_populates="query", cascade="all, delete-orphan")
    competitor_tracking = relationship("CompetitorTracking", back_populates="query")
    
    __table_args__ = (
        Index("idx_queries_active", "is_active"),
        Index("idx_queries_category", "category"),
        Index("idx_queries_priority", "priority"),
    )


class Citation(Base, TimestampMixin):
    """Citations found across different search engines."""
    __tablename__ = "citations"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    query_id = Column(PostgresUUID(as_uuid=True), ForeignKey("queries.id"), nullable=False)
    engine = Column(String(50), nullable=False)  # google, perplexity, chatgpt, etc.
    url = Column(Text, nullable=False)
    title = Column(Text)
    snippet = Column(Text)
    position = Column(Integer)
    citation_type = Column(String(50))  # ai_overview, featured_snippet, direct_answer, etc.
    source_domain = Column(String(255))
    prominence_score = Column(Float)  # 0.0 to 1.0
    metadata = Column(JSONB)
    
    # Relationships
    query = relationship("Query", back_populates="citations")
    
    __table_args__ = (
        Index("idx_citations_query_engine", "query_id", "engine"),
        Index("idx_citations_domain", "source_domain"),
        Index("idx_citations_type", "citation_type"),
        Index("idx_citations_position", "position"),
        Index("idx_citations_created", "created_at"),
        UniqueConstraint("query_id", "engine", "url", "created_at", name="uq_citation_snapshot"),
    )


class ContentAnalysis(Base, TimestampMixin):
    """Analysis results for content found in citations."""
    __tablename__ = "content_analysis"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(Text, nullable=False, unique=True)
    domain = Column(String(255), nullable=False)
    content_type = Column(String(50))  # article, landing_page, tool, etc.
    word_count = Column(Integer)
    schema_markup = Column(JSONB)
    authority_score = Column(Float)  # Domain authority
    freshness_score = Column(Float)  # Content freshness
    citation_count = Column(Integer, default=0)
    last_cited = Column(DateTime(timezone=True))
    last_analyzed = Column(DateTime(timezone=True), default=func.now())
    features = Column(JSONB)  # ML features extracted from content
    
    __table_args__ = (
        Index("idx_content_domain", "domain"),
        Index("idx_content_type", "content_type"),
        Index("idx_content_authority", "authority_score"),
        Index("idx_content_citation_count", "citation_count"),
        Index("idx_content_last_cited", "last_cited"),
    )


class CompetitorTracking(Base, TimestampMixin):
    """Competitor citation tracking and analysis."""
    __tablename__ = "competitor_tracking"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    competitor_domain = Column(String(255), nullable=False)
    query_id = Column(PostgresUUID(as_uuid=True), ForeignKey("queries.id"), nullable=False)
    engine = Column(String(50), nullable=False)
    citation_frequency = Column(Float)  # Citations per time period
    average_position = Column(Float)
    best_position = Column(Integer)
    content_types = Column(JSONB)  # Types of content getting cited
    trending_topics = Column(JSONB)
    last_citation = Column(DateTime(timezone=True))
    
    # Relationships
    query = relationship("Query", back_populates="competitor_tracking")
    
    __table_args__ = (
        Index("idx_competitor_domain", "competitor_domain"),
        Index("idx_competitor_query", "query_id"),
        Index("idx_competitor_engine", "engine"),
        Index("idx_competitor_frequency", "citation_frequency"),
        UniqueConstraint("competitor_domain", "query_id", "engine", name="uq_competitor_query_engine"),
    )


class ContentGap(Base, TimestampMixin):
    """Identified content gaps and opportunities."""
    __tablename__ = "content_gaps"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    query_text = Column(String(500), nullable=False)
    gap_type = Column(String(50), nullable=False)  # no_citations, weak_citations, competitor_dominated
    opportunity_score = Column(Float, nullable=False)  # 0.0 to 1.0
    suggested_content_type = Column(String(100))
    suggested_topics = Column(JSONB)
    competing_domains = Column(JSONB)
    search_volume = Column(Integer)
    difficulty_score = Column(Float)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="identified")  # identified, in_progress, addressed
    notes = Column(Text)
    
    __table_args__ = (
        Index("idx_gaps_opportunity_score", "opportunity_score"),
        Index("idx_gaps_type", "gap_type"),
        Index("idx_gaps_priority", "priority"),
        Index("idx_gaps_status", "status"),
        CheckConstraint("opportunity_score >= 0.0 AND opportunity_score <= 1.0", name="ck_opportunity_score_range"),
    )


class ActionItem(Base, TimestampMixin):
    """Generated action items and recommendations."""
    __tablename__ = "action_items"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    action_type = Column(String(50), nullable=False)  # create_content, optimize_content, distribution
    priority = Column(String(20), default="medium")
    estimated_effort = Column(String(20))  # low, medium, high
    expected_impact = Column(Float)  # 0.0 to 1.0
    related_query = Column(String(500))
    related_url = Column(Text)
    status = Column(String(20), default="pending")  # pending, in_progress, completed, cancelled
    assigned_to = Column(String(100))
    due_date = Column(DateTime(timezone=True))
    completion_notes = Column(Text)
    
    __table_args__ = (
        Index("idx_actions_type", "action_type"),
        Index("idx_actions_priority", "priority"),
        Index("idx_actions_status", "status"),
        Index("idx_actions_assigned", "assigned_to"),
        Index("idx_actions_due", "due_date"),
    )


class CitationHistory(Base):
    """Historical citation data for time-series analysis."""
    __tablename__ = "citation_history"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    query_id = Column(PostgresUUID(as_uuid=True), ForeignKey("queries.id"), nullable=False)
    engine = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    position = Column(Integer)
    citation_type = Column(String(50))
    prominence_score = Column(Float)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    __table_args__ = (
        Index("idx_history_query_engine_time", "query_id", "engine", "timestamp"),
        Index("idx_history_url_time", "url", "timestamp"),
        Index("idx_history_timestamp", "timestamp"),
    )


class SystemMetrics(Base, TimestampMixin):
    """System performance and health metrics."""
    __tablename__ = "system_metrics"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    labels = Column(JSONB)  # Additional metric labels
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    __table_args__ = (
        Index("idx_metrics_name_time", "metric_name", "timestamp"),
        Index("idx_metrics_type", "metric_type"),
        Index("idx_metrics_timestamp", "timestamp"),
    )