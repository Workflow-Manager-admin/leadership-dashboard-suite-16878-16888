from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.api.deps import get_db

router = APIRouter()

class ParsedResult(BaseModel):
    filename: str
    parsed_content: dict

# PUBLIC_INTERFACE
@router.post("/parse", summary="Parse a file", description="Trigger parsing of a previously uploaded file (stubbed: returns fake data)", response_model=ParsedResult)
async def parse_file(filename: str = Query("example.xlsx", description="Filename of uploaded file to parse"), db=Depends(get_db)):
    # TODO: Replace with actual file parser logic for Excel/Word/PDF/PPT
    # For demonstration, generate and persist fake structured result
    result = {"parsed": True, "content": {"sample": "Structured data for dashboard."}}
    await db["parsed_results"].update_one(
        {"filename": filename},
        {"$set": {"parsed_content": result}},
        upsert=True,
    )
    return ParsedResult(filename=filename, parsed_content=result)
