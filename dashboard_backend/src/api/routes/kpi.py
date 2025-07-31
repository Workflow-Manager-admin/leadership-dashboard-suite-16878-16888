from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

from src.api.models_kpi import (
    KPIMetricDefinition,
    KPIMetricCreate,
    KPIMetricUpdate,
)

router = APIRouter()


# --- KPI Metric CRUD API ---

# PUBLIC_INTERFACE
@router.post(
    "/metrics",
    summary="Create KPI metric definition",
    description="Define a new custom metric.",
    response_model=KPIMetricDefinition,
    status_code=201,
    tags=["KPI"]
)
async def create_kpi_metric(
    metric: KPIMetricCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create and store a new custom KPI metric."""
    kpi_id = str(uuid.uuid4())
    doc = {
        "kpi_id": kpi_id,
        "title": metric.title,
        "description": metric.description,
        "metric_type": metric.metric_type,
        "field": metric.field,
        "conditions": [c.dict() for c in (metric.conditions or [])]
    }
    await db.kpi_metrics.insert_one(doc)
    return KPIMetricDefinition(**doc)

# PUBLIC_INTERFACE
@router.get(
    "/metrics",
    summary="List all KPI metric definitions",
    description="Query all custom metrics defined.",
    response_model=List[KPIMetricDefinition],
    tags=["KPI"]
)
async def list_kpi_metrics(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """List all KPI metric definitions."""
    cursor = db.kpi_metrics.find()
    result = []
    async for doc in cursor:
        result.append(KPIMetricDefinition(**doc))
    return result

# PUBLIC_INTERFACE
@router.get(
    "/metrics/{kpi_id}",
    summary="Get KPI metric definition",
    description="Retrieve a KPI metric by its identifier.",
    response_model=KPIMetricDefinition,
    tags=["KPI"]
)
async def get_kpi_metric(
    kpi_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get metric definition by kpi_id."""
    doc = await db.kpi_metrics.find_one({"kpi_id": kpi_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Metric {kpi_id} not found")
    return KPIMetricDefinition(**doc)

# PUBLIC_INTERFACE
@router.put(
    "/metrics/{kpi_id}",
    summary="Update KPI metric definition",
    description="Edit a KPI metric's fields/conditions.",
    response_model=KPIMetricDefinition,
    tags=["KPI"]
)
async def update_kpi_metric(
    kpi_id: str, update: KPIMetricUpdate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update title, description, type, field, or conditions of metric."""
    doc = await db.kpi_metrics.find_one({"kpi_id": kpi_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Metric {kpi_id} not found")
    update_dict = {}
    if update.title is not None:
        update_dict["title"] = update.title
    if update.description is not None:
        update_dict["description"] = update.description
    if update.metric_type is not None:
        update_dict["metric_type"] = update.metric_type
    if update.field is not None:
        update_dict["field"] = update.field
    if update.conditions is not None:
        update_dict["conditions"] = [c.dict() for c in update.conditions]
    if update_dict:
        await db.kpi_metrics.update_one({"kpi_id": kpi_id}, {"$set": update_dict})
    new_doc = await db.kpi_metrics.find_one({"kpi_id": kpi_id})
    return KPIMetricDefinition(**new_doc)

# PUBLIC_INTERFACE
@router.delete(
    "/metrics/{kpi_id}",
    summary="Delete KPI metric",
    description="Remove a KPI metric definition.",
    status_code=204,
    tags=["KPI"]
)
async def delete_kpi_metric(
    kpi_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete the specified KPI metric by id."""
    res = await db.kpi_metrics.delete_one({"kpi_id": kpi_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Metric {kpi_id} not found")


# --- KPI Computation Engine/API (core business logic) ---

class KPIComputationRequest(BaseModel):
    filename: str = Field(..., description="Filename for which to compute KPIs")
    metric_ids: Optional[List[str]] = Field(None, description="Subset of metric ids to compute; if None, all defined KPIs applied.")

class KPIResult(BaseModel):
    kpis: Dict[str, Any]

class KPIStoredResult(BaseModel):
    filename: str
    kpis: Dict[str, Any]

def _flatten_sheet_rows(parsed_content):
    """
    Helper: Given parsed_content dict from Excel, returns a list of dicts.
    Only for Excel: {'type': 'excel', 'sheets': {sheet_name: [[header], [row], ...]}}.
    Returns list of dicts: [{"A": 1, "B": 2, ...}, ...]
    """
    if isinstance(parsed_content, dict) and parsed_content.get("type") == "excel":
        all_rows = []
        for sheet, data in parsed_content.get("sheets", {}).items():
            if not data or not isinstance(data, list) or len(data) < 2:
                continue
            headers = data[0]
            for row in data[1:]:
                # pad/truncate to same length as headers
                r = list(row) if isinstance(row, (list, tuple)) else []
                if len(r) < len(headers):
                    r += [None] * (len(headers) - len(r))
                elif len(r) > len(headers):
                    r = r[:len(headers)]
                all_rows.append(dict(zip(headers, r)))
        return all_rows
    # For other types, treat the content as a flat list if appropriate
    return []

def _apply_kpi_conditions(row, conditions: List[dict]):
    """Returns True if all conditions pass for row."""
    for cond in conditions:
        field_val = row.get(cond["field"])
        op = cond["op"]
        target = cond["value"]
        if op == "equals":
            if field_val != target:
                return False
        elif op == "contains":
            if isinstance(field_val, str):
                if str(target) not in field_val:
                    return False
            elif isinstance(field_val, list):
                if target not in field_val:
                    return False
            else:
                return False
        elif op == "gt":
            try:
                if not (field_val > target):
                    return False
            except Exception:
                return False
        elif op == "lt":
            try:
                if not (field_val < target):
                    return False
            except Exception:
                return False
        elif op == "in":
            if isinstance(target, list):
                if field_val not in target:
                    return False
            elif isinstance(field_val, list):
                if target not in field_val:
                    return False
            else:
                return False
        else:
            return False
    return True

def _compute_metric_on_rows(metric: KPIMetricDefinition, rows: List[dict]):
    filtrows = [r for r in rows if _apply_kpi_conditions(r, metric.conditions or [])]
    if metric.metric_type == "count":
        return len(filtrows)
    elif metric.metric_type in ("sum", "average"):
        field = metric.field
        if not field:
            return None
        vals = [r.get(field) for r in filtrows if r.get(field) is not None]
        nums = [v for v in vals if isinstance(v, (int, float))]
        if not nums:
            return None
        if metric.metric_type == "sum":
            return sum(nums)
        elif metric.metric_type == "average":
            return sum(nums) / len(nums)
    return None

# PUBLIC_INTERFACE
@router.post(
    "/compute",
    summary="Compute KPIs from metrics on parsed file",
    description="Compute each KPI according to all defined metric definitions for the given parsed document.",
    response_model=KPIResult
)
async def compute_kpis(
    request: KPIComputationRequest, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Compute KPIs for the given filename using saved metric definitions.
    """
    parsed_doc = await db.parsed.find_one({"filename": request.filename})
    if not parsed_doc or "parsed_content" not in parsed_doc:
        raise HTTPException(status_code=404, detail=f"No parsed content found for {request.filename}")
    metrics_cur = db.kpi_metrics.find(
        {"kpi_id": {"$in": request.metric_ids}} if request.metric_ids else {}
    )
    metric_list = []
    async for doc in metrics_cur:
        metric_list.append(KPIMetricDefinition(**doc))
    rows = _flatten_sheet_rows(parsed_doc["parsed_content"])
    results = {}
    for metric in metric_list:
        try:
            val = _compute_metric_on_rows(metric, rows)
            results[metric.kpi_id] = val
        except Exception:
            results[metric.kpi_id] = None
    # persist results
    await db.kpis.update_one(
        {"filename": request.filename},
        {"$set": {"filename": request.filename, "kpis": results}},
        upsert=True
    )
    return KPIResult(kpis=results)

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
