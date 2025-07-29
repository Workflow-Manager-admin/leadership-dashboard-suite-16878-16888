from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

class KPIRequest(BaseModel):
    filename: str = Field(..., description="Filename for which to calculate KPIs")

class KPIResult(BaseModel):
    kpis: Dict[str, Any]

class KPIStoredResult(BaseModel):
    filename: str
    kpis: Dict[str, Any]

# PUBLIC_INTERFACE
@router.post(
    "/compute",
    summary="Compute KPIs from data",
    description="Compute KPIs for given file (stubbed)",
    response_model=KPIResult
)
async def compute_kpis(
    request: KPIRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Compute KPIs for the given filename (stubbed, but store in MongoDB for listing later).
    """
    # Fake calculated KPI
    result = {"total_rows": 42, "sum_sales": 10000, "average_score": 84.2}
    await db.kpis.update_one(
        {"filename": request.filename},
        {"$set": {"filename": request.filename, "kpis": result}},
        upsert=True
    )
    return KPIResult(kpis=result)

# PUBLIC_INTERFACE
@router.get(
    "/computed",
    summary="List computed KPIs",
    description="List all computed KPIs for files (live from MongoDB).",
    response_model=List[KPIStoredResult]
)
async def list_computed_kpis(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    List all computed KPIs stored in MongoDB.
    """
    cursor = db.kpis.find()
    result = []
    async for doc in cursor:
        result.append(KPIStoredResult(filename=doc["filename"], kpis=doc["kpis"]))
    return result
