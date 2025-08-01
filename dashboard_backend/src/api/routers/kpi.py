"""
KPI computation and config APIs.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

class KPI(BaseModel):
    kpi_id: str
    name: str
    config: Dict[str, Any]

KPIS = {}

# PUBLIC_INTERFACE
@router.get("/", response_model=List[KPI], summary="List KPIs")
def list_kpis():
    return list(KPIS.values())

# PUBLIC_INTERFACE
@router.post("/", response_model=KPI, summary="Create new KPI")
def create_kpi(kpi: KPI):
    KPIS[kpi.kpi_id] = kpi
    return kpi

# PUBLIC_INTERFACE
@router.get("/{kpi_id}/compute", response_model=Dict[str, Any], summary="Compute KPI")
def compute_kpi(kpi_id: str):
    # TODO: Plug into business logic - call parse/aggregation/stat logic
    return {"kpi_id": kpi_id, "value": 42}
