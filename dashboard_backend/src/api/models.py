"""
ORM models using SQLAlchemy for all required dashboard_backend entities:
- FolderMapping, UploadedFile, ClassificationTag, Dashboard, Template, KPIResult, ParsedResult, Schedule
"""

from sqlalchemy import Column, String, Integer, Text, JSON, DateTime
from sqlalchemy.sql import func
from .db import Base

class FolderMapping(Base):
    __tablename__ = "folder_mappings"
    alias = Column(String, primary_key=True, index=True)
    path = Column(Text, nullable=False)

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(Text, unique=True, nullable=False, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

class ClassificationTag(Base):
    __tablename__ = "classification_tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(Text, nullable=False, index=True)
    tag = Column(String, nullable=False)

class Dashboard(Base):
    __tablename__ = "dashboards"
    dashboard_id = Column(String, primary_key=True, index=True)
    config = Column(JSON, nullable=False)

class Template(Base):
    __tablename__ = "templates"
    template_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    config = Column(JSON, nullable=False)

class KPIResult(Base):
    __tablename__ = "kpi_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(Text, nullable=False, unique=True, index=True)
    kpis = Column(JSON, nullable=False)

class ParsedResult(Base):
    __tablename__ = "parsed_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(Text, nullable=False, unique=True, index=True)
    parsed_content = Column(JSON, nullable=False)

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    dashboard_id = Column(String, nullable=False)
    cron = Column(String, nullable=False)
    email = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
