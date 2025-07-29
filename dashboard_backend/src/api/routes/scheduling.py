from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

class ScheduleRequest(BaseModel):
    dashboard_id: str = Field(..., description="Dashboard ID to schedule")
    cron: str = Field(..., description="Cron string for delivery schedule")
    email: str = Field(..., description="Recipient email address")

# PUBLIC_INTERFACE
@router.post("/", summary="Schedule dashboard report", description="API stub to schedule dashboard export via cron/email (no actual scheduling yet).")
async def schedule_report(
    req: ScheduleRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Insert a new schedule record in MongoDB.
    """
    await db.schedules.insert_one(req.model_dump())
    return {"scheduled": True}

# PUBLIC_INTERFACE
@router.get("/", summary="List scheduled reports", description="API stub for listing currently scheduled reports.", response_model=List[ScheduleRequest])
async def list_schedules(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all scheduled dashboard reports from MongoDB.
    """
    cursor = db.schedules.find()
    result = []
    async for doc in cursor:
        result.append(ScheduleRequest(**doc))
    return result
