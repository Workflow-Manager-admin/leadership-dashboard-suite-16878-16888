from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field

# Supported basic metric types
KPIType = Literal["sum", "average", "count"]

# PUBLIC_INTERFACE
class KPIMetricCondition(BaseModel):
    """A filter/condition for a KPI metric (applies to fields in doc content)."""
    field: str = Field(..., description="Dot-notated field to filter on (e.g. sheets.Sheet1.0.Project)")
    op: str = Field(..., description="Operator: equals | contains | gt | lt | in")
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(..., description="Value to be used in the filter operation.")

# PUBLIC_INTERFACE
class KPIMetricDefinition(BaseModel):
    """Definition of a dynamic KPI metric."""
    kpi_id: str = Field(..., description="Unique KPI/metric identifier")
    title: str = Field(..., description="Metric name/title")
    description: Optional[str] = Field(None, description="Human-friendly description")
    metric_type: KPIType = Field(..., description="Type of metric: sum | average | count")
    field: Optional[str] = Field(None, description="Field to compute sum/average on; not used for 'count'")
    conditions: Optional[List[KPIMetricCondition]] = Field(default_factory=list, description="List of filters (AND) to select applicable records")

# PUBLIC_INTERFACE
class KPIMetricCreate(BaseModel):
    """Request model for creating a KPI metric."""
    title: str
    description: Optional[str] = None
    metric_type: KPIType
    field: Optional[str] = None
    conditions: Optional[List[KPIMetricCondition]] = Field(default_factory=list)

# PUBLIC_INTERFACE
class KPIMetricUpdate(BaseModel):
    """Request model for updating a KPI metric."""
    title: Optional[str] = None
    description: Optional[str] = None
    metric_type: Optional[KPIType] = None
    field: Optional[str] = None
    conditions: Optional[List[KPIMetricCondition]] = None

