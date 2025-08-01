"""
Export dashboard and KPI data to various formats.
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter()

# PUBLIC_INTERFACE
@router.get("/pdf", response_class=StreamingResponse, summary="Export dashboard to PDF")
def export_pdf(dashboard_id: str = Query(...)):
    # TODO: Generate actual PDF from dashboard_id
    def fake_stream():
        yield b"%PDF-1.4\n<!-- Simulated PDF binary -->"
    return StreamingResponse(fake_stream(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={dashboard_id}.pdf"})

# PUBLIC_INTERFACE
@router.get("/ppt", response_class=StreamingResponse, summary="Export dashboard to PPTX")
def export_ppt(dashboard_id: str = Query(...)):
    def fake_stream():
        yield b"Simulated PPTX content"
    return StreamingResponse(fake_stream(), media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            headers={"Content-Disposition": f"attachment; filename={dashboard_id}.pptx"})

# PUBLIC_INTERFACE
@router.get("/html", response_class=StreamingResponse, summary="Export dashboard to HTML")
def export_html(dashboard_id: str = Query(...)):
    def fake_stream():
        yield b"<html><body>Simulated HTML Export</body></html>"
    return StreamingResponse(fake_stream(), media_type="text/html",
                            headers={"Content-Disposition": f"attachment; filename={dashboard_id}.html"})
