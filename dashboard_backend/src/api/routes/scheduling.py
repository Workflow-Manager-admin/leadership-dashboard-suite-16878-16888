from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, EmailStr
from typing import List
from src.api.deps import get_db
from src.api.routes.auth import get_current_active_user
from src.api.security import rate_limit

router = APIRouter()

class ScheduleRequest(BaseModel):
    dashboard_id: str = Field(..., min_length=1, max_length=100, description="Dashboard ID to schedule")
    cron: str = Field(..., min_length=6, max_length=64, description="Cron string for delivery schedule")
    email: EmailStr = Field(..., description="Recipient email address")

# PUBLIC_INTERFACE
@router.post(
    "/",
    summary="Schedule dashboard report",
    description="API stub to schedule dashboard export via cron/email (no actual scheduling yet)."
)
@rate_limit(5, 60)
async def schedule_report(
    request: Request,
    req: ScheduleRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    await db["schedules"].insert_one(req.model_dump())
    return {"scheduled": True}

# PUBLIC_INTERFACE
@router.get(
    "/",
    summary="List scheduled reports",
    description="API stub for listing currently scheduled reports.",
    response_model=List[ScheduleRequest]
)
@rate_limit(10, 60)
async def list_schedules(
    request: Request,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    schedules = await db["schedules"].find({}).to_list(length=100)
    return [ScheduleRequest(**{k: v for k, v in s.items() if k in ScheduleRequest.model_fields}) for s in schedules]
