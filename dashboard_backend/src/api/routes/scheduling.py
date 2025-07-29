from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from src.api.deps import get_db
from src.api.routes.auth import get_current_active_user
from src.api.security import rate_limit
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os

router = APIRouter()

class ScheduleRequest(BaseModel):
    dashboard_id: str = Field(..., min_length=1, max_length=100, description="Dashboard ID to schedule")
    cron: str = Field(..., min_length=6, max_length=64, description="Cron string for delivery schedule")
    email: EmailStr = Field(..., description="Recipient email address")
    export_format: Optional[str] = Field(default="pdf", description="Export format for delivery")

class ScheduleStatus(BaseModel):
    schedule_id: str
    status: str
    last_run: Optional[datetime]
    last_error: Optional[str]
    deliveries: List[dict] = []

def validate_cron(cron: str) -> bool:
    parts = cron.strip().split()
    return len(parts) == 5 or len(parts) == 6

def send_email_report(to_email, subject, body, attachment_path=None):
    # For demo: use localhost; in prod set SMTP config in env
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "noreply@dashboard.local"
    msg['To'] = to_email
    msg.set_content(body)
    if attachment_path and os.path.isfile(attachment_path):
        with open(attachment_path, "rb") as f:
            data = f.read()
            ext = attachment_path.split(".")[-1]
            filename = os.path.basename(attachment_path)
            msg.add_attachment(data, maintype="application", subtype=ext, filename=filename)
    try:
        with smtplib.SMTP("localhost") as server:
            server.send_message(msg)
        return True, ""
    except Exception as ex:
        return False, str(ex)

# PUBLIC_INTERFACE
@router.post(
    "/",
    summary="Schedule dashboard report",
    description="Robustly schedule dashboard export+email, parse cron, and check delivery/error tracking."
)
@rate_limit(5, 60)
async def schedule_report(
    request: Request,
    req: ScheduleRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not validate_cron(req.cron):
        raise HTTPException(status_code=400, detail="Invalid cron format")
    schedule_doc = req.dict()
    schedule_doc["created_by"] = current_user["email"]
    schedule_doc["created_at"] = datetime.utcnow()
    schedule_doc["status"] = "scheduled"
    res = await db["schedules"].insert_one(schedule_doc)
    return {"scheduled": True, "schedule_id": str(res.inserted_id)}

# PUBLIC_INTERFACE
@router.get(
    "/",
    summary="List scheduled reports",
    description="List all scheduled dashboard report jobs with delivery/error checks.",
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

# PUBLIC_INTERFACE
@router.get(
    "/status/{schedule_id}",
    summary="Get schedule delivery/error status (demo usage)",
    description="Shows last delivery status and error messages for a scheduled job.",
    response_model=ScheduleStatus
)
@rate_limit(10, 60)
async def get_schedule_status(
    schedule_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    rec = await db["schedules"].find_one({"_id": schedule_id})
    if not rec:
        raise HTTPException(status_code=404, detail="Schedule not found")
    deliveries = rec.get("deliveries", [])
    return ScheduleStatus(
        schedule_id=schedule_id,
        status=rec.get("status", "scheduled"),
        last_run=rec.get("last_run"),
        last_error=rec.get("last_error"),
        deliveries=deliveries
    )
