from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class UploadEntity(BaseModel):
    """Represents an uploaded file record."""
    filename: str = Field(..., description="Name of uploaded file")
    status: str = Field(..., description="Upload or ingestion status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata about the upload (user, size, etc.)")


# PUBLIC_INTERFACE
class FolderMappingEntity(BaseModel):
    """Represents a mapped/monitored folder."""
    path: str = Field(..., description="Absolute or relative folder path to monitor")
    alias: str = Field(..., description="Custom name/label for the folder")


# PUBLIC_INTERFACE
class DashboardConfigEntity(BaseModel):
    """Represents a dashboard configuration."""
    dashboard_id: str = Field(..., description="Unique dashboard identifier")
    config: Dict[str, Any] = Field(..., description="Dashboard configuration (structure, widgets, filters etc.)")


# PUBLIC_INTERFACE
class TemplateEntity(BaseModel):
    """Represents a dashboard template."""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    config: Dict[str, Any] = Field(..., description="Template dashboard configuration")


# PUBLIC_INTERFACE
class ScheduleEntity(BaseModel):
    """Represents a scheduled dashboard report/email."""
    dashboard_id: str = Field(..., description="Dashboard ID to schedule")
    cron: str = Field(..., description="Cron string for delivery schedule")
    email: str = Field(..., description="Recipient email address")

# PUBLIC_INTERFACE
class ClassificationResultEntity(BaseModel):
    """Represents the result of a classification/tagging process."""
    filename: str = Field(..., description="Filename to classify/tag")
    tags: List[str] = Field(..., description="Manual or rule-based tags")
