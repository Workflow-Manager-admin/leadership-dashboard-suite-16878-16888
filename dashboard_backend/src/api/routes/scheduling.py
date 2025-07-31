from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.api.utils.scheduler_utils import scheduler_singleton

router = APIRouter()

class ScheduleRequest(BaseModel):
    dashboard_id: str = Field(..., description="Dashboard ID to schedule")
    cron: str = Field(..., description="Cron string for delivery schedule")
    email: str = Field(..., description="Recipient email address")
    report_type: str = Field(..., description="Report type (pdf, ppt, html)")

class ScheduleResponse(ScheduleRequest):
    id: str = Field(..., description="Schedule identifier")


# PUBLIC_INTERFACE
@router.post(
    "/",
    summary="Schedule dashboard report",
    description="Schedule a recurring dashboard export (PDF/PPT/HTML) to be sent by email via SMTP at the specified cron schedule.",
    response_model=ScheduleResponse,
    status_code=201,
    tags=["Scheduling"]
)
async def create_schedule(
    req: ScheduleRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Insert a new schedule record in MongoDB and start the scheduled background job for emailing reports.
    """
    # Generate a unique schedule id (deterministic for dashboard/recipient/report_type to prevent duplicates)
    import hashlib, json
    schedule_id = hashlib.sha1(
        json.dumps([req.dashboard_id, req.email, req.cron, req.report_type], sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]

    # Upsert by schedule id
    schedule_doc = dict(req.model_dump())
    schedule_doc["id"] = schedule_id
    await db.schedules.update_one({"id": schedule_id}, {"$set": schedule_doc}, upsert=True)
    scheduler_singleton.add_or_update_job(schedule_id, req.dashboard_id, req.cron, req.email, req.report_type)
    return ScheduleResponse(**schedule_doc)


# PUBLIC_INTERFACE
@router.get(
    "/",
    summary="List scheduled reports",
    description="List all scheduled dashboard export jobs and their details.",
    response_model=List[ScheduleResponse],
    tags=["Scheduling"]
)
async def list_schedules(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all scheduled dashboard report jobs from MongoDB.
    """
    cursor = db.schedules.find()
    result = []
    async for doc in cursor:
        result.append(ScheduleResponse(**doc))
    return result


# PUBLIC_INTERFACE
@router.put(
    "/{schedule_id}",
    summary="Update a scheduled report",
    description="Update the details for an existing scheduled report (cron, recipient, report type).",
    response_model=ScheduleResponse,
    tags=["Scheduling"]
)
async def update_schedule(
    schedule_id: str,
    req: ScheduleRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update an existing schedule and re-create the background scheduled job.
    """
    doc = await db.schedules.find_one({"id": schedule_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.schedules.update_one({"id": schedule_id}, {"$set": req.model_dump()})
    scheduler_singleton.add_or_update_job(schedule_id, req.dashboard_id, req.cron, req.email, req.report_type)
    merged = dict(req.model_dump()); merged["id"] = schedule_id
    return ScheduleResponse(**merged)

# PUBLIC_INTERFACE
@router.delete(
    "/{schedule_id}",
    summary="Delete a scheduled report",
    description="Delete a scheduled dashboard email/report and remove its background job.",
    status_code=204,
    tags=["Scheduling"]
)
async def delete_schedule(
    schedule_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete the scheduled report by schedule_id.
    """
    res = await db.schedules.delete_one({"id": schedule_id})
    scheduler_singleton.remove_job_if_exists(schedule_id)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return

# PUBLIC_INTERFACE
@router.get(
    "/{schedule_id}",
    summary="Get scheduled report details",
    description="Get details for a particular scheduled dashboard report.",
    response_model=ScheduleResponse,
    tags=["Scheduling"]
)
async def get_schedule(
    schedule_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Retrieve a scheduled dashboard report definition.
    """
    doc = await db.schedules.find_one({"id": schedule_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse(**doc)

