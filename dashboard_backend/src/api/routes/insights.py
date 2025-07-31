from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.api.db import get_database
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter()

# --- Models ---

# PUBLIC_INTERFACE
class InsightSummary(BaseModel):
    """Summary insight object for a file, KPI set, or dashboard."""
    filename: Optional[str] = Field(None, description="Filename if applicable")
    summary: str = Field(..., description="High-level summary insight (natural language)")
    highlights: List[str] = Field(..., description="List of highlight events, trends, or outliers")
    kpi_changes: Optional[List[dict]] = Field(None, description="Key changes or anomalies in KPIs")

# PUBLIC_INTERFACE
class InsightsResponse(BaseModel):
    """Response model: insights collection."""
    insights: List[InsightSummary]


# --- Helper Functions ---

async def collect_kpi_trends(db: AsyncIOMotorDatabase, filename: Optional[str] = None):
    """Analyze KPIs for trends, outliers, and generate highlight strings."""
    query = {"filename": filename} if filename else {}
    cursor = db.kpis.find(query)
    results = []
    async for doc in cursor:
        res = {"filename": doc["filename"], "kpis": doc["kpis"]}
        results.append(res)
    return results

def basic_stats_for_kpi(values):
    """Return mean, std, min, max or None if not enough values."""
    # Ignore None or NaN values
    arr = np.array([v for v in values if isinstance(v, (int, float))])
    if len(arr) == 0:
        return None
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "count": int(len(arr))
    }

def generate_kpi_highlights(kpi_stats: Dict[str, Dict], file_kpis: List[Dict]):
    highlights = []
    for kpi_id, stats in kpi_stats.items():
        if not stats:
            continue
        for row in file_kpis:
            val = row["kpis"].get(kpi_id)
            filename = row.get("filename", "<unknown>")
            # Outlier: more than 2 std dev from mean
            if val is not None and stats["std"] > 0:
                if abs(val - stats["mean"]) > 2 * stats["std"]:
                    highlight = f"Outlier in {kpi_id} for {filename}: {val} (mean={stats['mean']:.2f})"
                    highlights.append(highlight)
    return highlights

def basic_narrative_for_kpis(file_kpi: Dict, kpi_stats: Dict[str, Dict]) -> str:
    if not kpi_stats or not file_kpi:
        return "No data available for insights."
    parts = []
    for kpi_id, stats in kpi_stats.items():
        val = file_kpi["kpis"].get(kpi_id)
        if val is not None and stats:
            # Simple trend or flag
            if val > stats["mean"]:
                parts.append(f"{kpi_id} is above average ({val} vs avg {stats['mean']:.2f})")
            elif val < stats["mean"]:
                parts.append(f"{kpi_id} is below average ({val} vs avg {stats['mean']:.2f})")
            else:
                parts.append(f"{kpi_id} matches average ({val})")
    return " | ".join(parts) or "No notable KPI trends detected."


# --- REST Endpoints ---

# PUBLIC_INTERFACE
@router.get(
    "/summary",
    summary="Get summary insights and highlights",
    description="Compute and return summary insights (trends, anomalies, highlights) from all parsed files and computed KPIs.",
    response_model=InsightsResponse,
    tags=["Insights"]
)
async def get_summary_insights(
    filename: Optional[str] = Query(None, description="If provided, restrict insights to a single file"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Aggregate KPIs and parsed data to produce human-readable insights, trends, and highlights
    for leadership dashboards. Optionally restrict to one file.
    """
    # Retrieve all computed KPIs (filtered by filename if set)
    all_file_kpis = await collect_kpi_trends(db, filename)
    if not all_file_kpis:
        return InsightsResponse(insights=[])
    # Gather stats for all kpi_ids
    all_kpi_ids = set()
    for row in all_file_kpis:
        all_kpi_ids.update(row["kpis"].keys())
    kpi_stats = {}
    for kpi_id in all_kpi_ids:
        values = [r["kpis"].get(kpi_id) for r in all_file_kpis]
        kpi_stats[kpi_id] = basic_stats_for_kpi(values)
    # Generate summaries per file
    insights = []
    for row in all_file_kpis:
        summary = basic_narrative_for_kpis(row, kpi_stats)
        highlight_list = []
        # Flag big changes for this file
        for kpi_id, val in row["kpis"].items():
            stats = kpi_stats.get(kpi_id)
            if stats and stats["std"] > 0 and abs(val - stats["mean"]) > 2 * stats["std"]:
                highlight_list.append(f"{kpi_id}: unusual value {val} (average {stats['mean']:.2f})")
        highlights = highlight_list
        insights.append(
            InsightSummary(
                filename=row.get("filename"),
                summary=summary,
                highlights=highlights
            )
        )
    # Compute overall highlights
    additional_highlights = generate_kpi_highlights(kpi_stats, all_file_kpis)
    if not filename and additional_highlights:
        # Attach a global summary
        insights.insert(
            0, InsightSummary(
                filename=None,
                summary="System-wide outliers and anomalies detected.",
                highlights=additional_highlights
            )
        )
    return InsightsResponse(insights=insights)

