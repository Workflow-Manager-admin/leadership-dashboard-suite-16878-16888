"""
Report scheduling & summary/insights APIs.
"""
from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ScheduleConfig(BaseModel):
    schedule_id: str
    dashboard_id: str
    recipients: List[str]
    cron: str
    format: str

SCHEDULES = {}

# PUBLIC_INTERFACE
@router.get("/", response_model=List[ScheduleConfig], summary="List schedules")
def list_schedules():
    return list(SCHEDULES.values())

# PUBLIC_INTERFACE
@router.post("/", response_model=ScheduleConfig, summary="Create schedule")
def create_schedule(cfg: ScheduleConfig, background_tasks: BackgroundTasks):
    # TODO: Add background task for scheduled export/email
    SCHEDULES[cfg.schedule_id] = cfg
    return cfg

# PUBLIC_INTERFACE
@router.post("/run", summary="Run report delivery now")
def run_now(schedule_id: str, background_tasks: BackgroundTasks):
    # TODO: Trigger manual report/send logic.
    return {"schedule_id": schedule_id, "status": "executed"}

# PUBLIC_INTERFACE
@router.get("/summary", summary="Get dashboard summary/highlights")
def get_summary(dashboard_id: str = Query(...)):
    # TODO: Business logic for summary
    return {"dashboard_id": dashboard_id, "highlights": ["Sample accomplishment", "Red flag: budget risk"]}
