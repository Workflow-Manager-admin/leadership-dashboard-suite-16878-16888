from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.api.models import ParsedResult as ParsedResultORM
from src.api.deps import get_db

router = APIRouter()

class ParsedResult(BaseModel):
    filename: str
    parsed_content: dict

# PUBLIC_INTERFACE
@router.post("/parse", summary="Parse a file", description="Trigger parsing of a previously uploaded file (stubbed: returns fake data)", response_model=ParsedResult)
async def parse_file(filename: str = Query("example.xlsx", description="Filename of uploaded file to parse"), db: Session = Depends(get_db)):
    # TODO: Replace with actual file parser logic for Excel/Word/PDF/PPT
    # For demonstration, generate and persist fake structured result
    result = {"parsed": True, "content": {"sample": "Structured data for dashboard."}}
    db_obj = db.query(ParsedResultORM).filter_by(filename=filename).first()
    if db_obj:
        db_obj.parsed_content = result
    else:
        db_obj = ParsedResultORM(filename=filename, parsed_content=result)
        db.add(db_obj)
    db.commit()
    return ParsedResult(filename=filename, parsed_content=result)
