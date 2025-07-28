from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()

# In-memory scheduled reports
SCHEDULES = []

class ScheduleRequest(BaseModel):
    dashboard_id: str = Field(..., description="Dashboard ID to schedule")
    cron: str = Field(..., description="Cron string for delivery schedule")
    email: str = Field(..., description="Recipient email address")

# PUBLIC_INTERFACE
@router.post("/", summary="Schedule dashboard report", description="API stub to schedule dashboard export via cron/email (no actual scheduling yet).")
async def schedule_report(req: ScheduleRequest):
    SCHEDULES.append(req)
    return {"scheduled": True}

# PUBLIC_INTERFACE
@router.get("/", summary="List scheduled reports", description="API stub for listing currently scheduled reports.", response_model=List[ScheduleRequest])
async def list_schedules():
    return SCHEDULES
