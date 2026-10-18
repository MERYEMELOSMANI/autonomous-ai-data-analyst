import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class DatasetModel(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    duckdb_table_name = Column(String(64), nullable=False, unique=True)
    columns_json = Column(JSON, nullable=True)
    quality_report_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("AnalysisSessionModel", back_populates="dataset", cascade="all, delete-orphan")
    reports = relationship("ReportModel", back_populates="dataset", cascade="all, delete-orphan")

class AnalysisSessionModel(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False, default="New Analysis")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("DatasetModel", back_populates="sessions")
    messages = relationship("AnalysisMessageModel", back_populates="session", cascade="all, delete-orphan")

class AnalysisMessageModel(Base):
    __tablename__ = "analysis_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    evidence_json = Column(JSON, nullable=True)
    visualizations_json = Column(JSON, nullable=True)
    timeline_json = Column(JSON, nullable=True)
    status = Column(String(20), default="completed")
    workflow_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("AnalysisSessionModel", back_populates="messages")

class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), nullable=True)
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=False)
    methodology = Column(Text, nullable=False)
    findings_json = Column(JSON, nullable=True)
    visualizations_json = Column(JSON, nullable=True)
    limitations_json = Column(JSON, nullable=True)
    conclusions_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("DatasetModel", back_populates="reports")

class WorkflowRunModel(Base):
    __tablename__ = "workflow_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), nullable=True)
    dataset_id = Column(String(36), nullable=False)
    query = Column(Text, nullable=False)
    status = Column(String(20), default="running")  # running, completed, failed
    plan_json = Column(JSON, nullable=True)
    steps_json = Column(JSON, nullable=True)
    duration_ms = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
