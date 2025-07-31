import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from aiosmtplib import SMTP
from email.message import EmailMessage
import traceback

from src.api.db import MongoDB
from src.api.utils import export_utils

# PUBLIC_INTERFACE
class ReportScheduler:
    """Singleton class to manage scheduled report jobs."""
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.started = False

    def ensure_started(self):
        if not self.started:
            self.scheduler.start()
            self.started = True

    # PUBLIC_INTERFACE
    def add_or_update_job(self, job_id, dashboard_id, cron, email, report_type):
        self.ensure_started()
        self.remove_job_if_exists(job_id)
        self.scheduler.add_job(
            scheduled_report_job,
            CronTrigger.from_crontab(cron),
            id=job_id,
            args=[dashboard_id, email, report_type],
            replace_existing=True,
            name=f"scheduled_report_{job_id}"
        )

    # PUBLIC_INTERFACE
    def remove_job_if_exists(self, job_id):
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    # PUBLIC_INTERFACE
    def shutdown(self):
        if self.started:
            self.scheduler.shutdown()


scheduler_singleton = ReportScheduler()

# PUBLIC_INTERFACE
def start_scheduler_once():
    """Call during FastAPI startup."""
    scheduler_singleton.ensure_started()


async def scheduled_report_job(dashboard_id, email, report_type):
    """Background scheduled task: generate report and send email."""
    try:
        db = MongoDB.get_db()  # MongoDB async client
        dashboard = await db.dashboards.find_one({"dashboard_id": dashboard_id})
        if not dashboard:
            print(f"[Scheduler] Dashboard {dashboard_id} not found for scheduled report.")
            return

        config = dashboard["config"]
        filename_base = f"{dashboard_id}_scheduled_export"
        # Choose format handling
        fmt = report_type.lower()
        tmp_dir = "/tmp"
        if fmt == "html":
            html = export_utils.dashboard_to_html(config)
            tmpfile = os.path.join(tmp_dir, f"{filename_base}.html")
            with open(tmpfile, "w", encoding="utf-8") as f:
                f.write(html)
            mime_type = "text/html"
        elif fmt == "pdf":
            html = export_utils.dashboard_to_html(config)
            tmpfile = os.path.join(tmp_dir, f"{filename_base}.pdf")
            export_utils.generate_pdf_from_html(html, tmpfile)
            mime_type = "application/pdf"
        elif fmt == "ppt":
            tmpfile = os.path.join(tmp_dir, f"{filename_base}.pptx")
            export_utils.generate_ppt_from_dashboard(config, tmpfile)
            mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        else:
            print(f"[Scheduler] Invalid format: {fmt} (skipped sending)")
            return

        subject = f"Scheduled Dashboard Report: {dashboard_id}"
        body = f"Please find the scheduled {fmt.upper()} report attached for dashboard: {dashboard_id}."
        await send_email_with_attachment(email, subject, body, tmpfile, mime_type)
    except Exception:
        print(f"[Scheduler] Error in scheduled_report_job: {traceback.format_exc()}")


# PUBLIC_INTERFACE
async def send_email_with_attachment(
    to_email: str, subject: str, body: str, attachment_path: str, mime_type: str
):
    """Send email using SMTP with file attachment."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    # Add file attachment
    with open(attachment_path, "rb") as f:
        file_data = f.read()
        filename = os.path.basename(attachment_path)
        maintype, subtype = mime_type.split("/", 1)
        msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=filename)

    smtp = SMTP(hostname=smtp_host, port=smtp_port, use_tls=False)
    await smtp.connect()
    await smtp.starttls()
    await smtp.login(smtp_user, smtp_password)
    await smtp.send_message(msg)
    await smtp.quit()
