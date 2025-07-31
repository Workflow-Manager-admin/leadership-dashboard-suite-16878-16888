from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class RuleCondition(BaseModel):
    """A single atomic condition in a rule for document tagging/classification."""
    field: str = Field(..., description="Path within parsed_content (support dot notation for nested keys)")
    op: str = Field(..., description="Operator: one of 'equals', 'contains', 'regex', 'gt', 'lt', 'in'")
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(..., description="Value to match, list or scalar as per op")

# PUBLIC_INTERFACE
class ClassificationRuleEntity(BaseModel):
    """Represents a rule for classifying/tagging documents after parsing."""
    rule_id: str = Field(..., description="Unique identifier for the rule")
    description: str = Field(..., description="Description of what this rule does")
    conditions: List[RuleCondition] = Field(..., description="List of conditions to match all (AND logic)")
    tags: List[str] = Field(..., description="Tags to assign if the rule matches")

# PUBLIC_INTERFACE
class RuleCreateEntity(BaseModel):
    """Request model for creating a classification/tagging rule."""
    description: str = Field(..., description="Description of the new rule")
    conditions: List[RuleCondition] = Field(..., description="AND-list of match conditions")
    tags: List[str] = Field(..., description="Tags to assign if rule matches")

# PUBLIC_INTERFACE
class RuleUpdateEntity(BaseModel):
    """Request model for updating an existing rule."""
    description: Optional[str] = Field(None, description="(Optional) New description")
    conditions: Optional[List[RuleCondition]] = Field(None, description="(Optional) Replace rule conditions (AND semantics)")
    tags: Optional[List[str]] = Field(None, description="(Optional) Replace tags for this rule")

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
    """Represents a user-owned dashboard configuration."""
    dashboard_id: str = Field(..., description="Unique dashboard identifier")
    user_id: str = Field(..., description="Owner user id")
    config: Dict[str, Any] = Field(..., description="Dashboard configuration (structure, widgets, filters etc.)")


# PUBLIC_INTERFACE
class TemplateEntity(BaseModel):
    """Represents a user-owned dashboard template."""
    template_id: str = Field(..., description="Unique template identifier")
    user_id: str = Field(..., description="Owner user id")
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

# --- Insights/Highlight API Models ---

# PUBLIC_INTERFACE
class InsightSummaryEntity(BaseModel):
    """Summary insight entity for reporting trends/outliers/highlights."""
    filename: str = Field(None, description="Filename")
    summary: str = Field(..., description="Summary statement for the file or dataset")
    highlights: List[str] = Field(..., description="List of highlight strings")

# PUBLIC_INTERFACE
class InsightsAPIResponse(BaseModel):
    """API response for insights/highlights."""
    insights: List[InsightSummaryEntity]

