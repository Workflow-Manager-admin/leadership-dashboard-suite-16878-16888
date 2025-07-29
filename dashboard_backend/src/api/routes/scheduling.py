from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List

from src.api.deps import get_db

router = APIRouter()

class ScheduleRequest(BaseModel):
    dashboard_id: str = Field(..., description="Dashboard ID to schedule")
    cron: str = Field(..., description="Cron string for delivery schedule")
    email: str = Field(..., description="Recipient email address")

# PUBLIC_INTERFACE
@router.post("/", summary="Schedule dashboard report", description="API stub to schedule dashboard export via cron/email (no actual scheduling yet).")
async def schedule_report(req: ScheduleRequest, db=Depends(get_db)):
    await db["schedules"].insert_one(req.model_dump())
    return {"scheduled": True}

# PUBLIC_INTERFACE
@router.get("/", summary="List scheduled reports", description="API stub for listing currently scheduled reports.", response_model=List[ScheduleRequest])
async def list_schedules(db=Depends(get_db)):
    schedules = await db["schedules"].find({}).to_list(length=100)
    return [ScheduleRequest(**{k: v for k, v in s.items() if k in ScheduleRequest.model_fields}) for s in schedules]
