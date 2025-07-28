from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any

router = APIRouter()

# In-memory computed KPIs (stubbed)
KPI_RESULTS = {}

class KPIRequest(BaseModel):
    filename: str = Field(..., description="Filename for which to calculate KPIs")

class KPIResult(BaseModel):
    kpis: Dict[str, Any]

# PUBLIC_INTERFACE
@router.post("/compute", summary="Compute KPIs from data", description="Compute KPIs for given file (stubbed)", response_model=KPIResult)
async def compute_kpis(request: KPIRequest):
    # Fake calculated KPI
    result = {"total_rows": 42, "sum_sales": 10000, "average_score": 84.2}
    KPI_RESULTS[request.filename] = result
    return KPIResult(kpis=result)
