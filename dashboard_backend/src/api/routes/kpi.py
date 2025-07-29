from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from src.api.deps import get_db
from src.api.routes.auth import get_current_active_user
from src.api.security import rate_limit

router = APIRouter()

class KPIRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=128, description="Filename for which to calculate KPIs")
    rules: Optional[List[str]] = Field(default=None, description="Custom business rules for KPI computation")
    # Optionally allow passing metric configs

class KPIResult(BaseModel):
    kpis: Dict[str, Any]

def excel_kpi(parsed_content: dict):
    import numpy as np
    kpis = {}
    rows = parsed_content.get("rows", []) if parsed_content else []
    if rows:
        kpis["row_count"] = len(rows)
        for col in parsed_content.get("columns", []):
            vals = [r[col] for r in rows if col in r and isinstance(r[col], (int, float, np.integer, np.floating))]
            if vals:
                kpis[f"{col.lower()}_sum"] = float(np.nansum(vals))
                kpis[f"{col.lower()}_mean"] = float(np.nanmean(vals))
    return kpis

def pdf_kpi(parsed_content: dict):
    return {
        "page_count": len(parsed_content.get("pages", [])),
        "has_summary": any("summary" in (p or "").lower() for p in parsed_content.get("pages", [])),
    }

def word_kpi(parsed_content: dict):
    txt = parsed_content.get("content", "")
    return {
        "word_count": len(txt.split()),
        "contains_action": "action" in txt.lower(),
    }

def ppt_kpi(parsed_content: dict):
    return {
        "slide_count": len(parsed_content.get("slides", [])),
        "has_team": any("team" in (s or "").lower() for s in parsed_content.get("slides", [])),
    }

# PUBLIC_INTERFACE
@router.post(
    "/compute",
    summary="Compute KPIs from data",
    description="Compute KPIs for given file (supports custom logic for Excel, PPT, PDF, Word)",
    response_model=KPIResult,
)
@rate_limit(10, 60)
async def compute_kpis(
    request: Request,
    req: KPIRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    parsed = await db["parsed_results"].find_one({"filename": req.filename})
    if not parsed:
        raise HTTPException(status_code=404, detail="Parsed result not found.")
    data = parsed.get("parsed_content", {})
    kind = data.get("type")
    if kind == "excel":
        result = excel_kpi(data)
    elif kind == "pdf":
        result = pdf_kpi(data)
    elif kind == "word":
        result = word_kpi(data)
    elif kind == "ppt":
        result = ppt_kpi(data)
    else:
        result = {"info": "No custom KPI logic for file type"}
    # Extra: allow custom rules
    if req.rules:
        for rule in req.rules:
            if rule == "row_more_than_10":
                result["row_count_gt_10"] = result.get("row_count", 0) > 10
    await db["kpi_results"].update_one(
        {"filename": req.filename},
        {"$set": {"kpis": result}},
        upsert=True,
    )
    return KPIResult(kpis=result)
