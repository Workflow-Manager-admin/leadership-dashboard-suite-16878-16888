from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Simple in-memory placeholder for parsed data
PARSED_DATA = {}

class ParsedResult(BaseModel):
    filename: str
    parsed_content: dict

# PUBLIC_INTERFACE
@router.post("/parse", summary="Parse a file", description="Trigger parsing of a previously uploaded file (stubbed: returns fake data)", response_model=ParsedResult)
async def parse_file(filename: str = "example.xlsx"):
    parsed = {"parsed": True, "content": "Sample structured data."}
    PARSED_DATA[filename] = parsed
    return ParsedResult(filename=filename, parsed_content=parsed)
