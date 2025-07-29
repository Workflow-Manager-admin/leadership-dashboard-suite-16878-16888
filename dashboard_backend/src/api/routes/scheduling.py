from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List
from sqlalchemy.orm import Session

from src.api.models import Schedule as ScheduleORM
from src.api.deps import get_db

router = APIRouter()

class ScheduleRequest(BaseModel):
    dashboard_id: str = Field(..., description="Dashboard ID to schedule")
    cron: str = Field(..., description="Cron string for delivery schedule")
    email: str = Field(..., description="Recipient email address")

# PUBLIC_INTERFACE
@router.post("/", summary="Schedule dashboard report", description="API stub to schedule dashboard export via cron/email (no actual scheduling yet).")
async def schedule_report(req: ScheduleRequest, db: Session = Depends(get_db)):
    db_obj = ScheduleORM(dashboard_id=req.dashboard_id, cron=req.cron, email=req.email)
    db.add(db_obj)
    db.commit()
    return {"scheduled": True}

# PUBLIC_INTERFACE
@router.get("/", summary="List scheduled reports", description="API stub for listing currently scheduled reports.", response_model=List[ScheduleRequest])
async def list_schedules(db: Session = Depends(get_db)):
    schedules = db.query(ScheduleORM).all()
    return [ScheduleRequest(dashboard_id=s.dashboard_id, cron=s.cron, email=s.email) for s in schedules]
