from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

class ParsedResult(BaseModel):
    filename: str
    parsed_content: dict

# PUBLIC_INTERFACE
@router.post(
    "/parse",
    summary="Parse a file",
    description="Trigger parsing of a previously uploaded file (stubbed: returns fake data)",
    response_model=ParsedResult,
)
async def parse_file(filename: str = "example.xlsx", db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Parse a file and store the parsed data in MongoDB (stub: always returns mocked data).
    """
    parsed = {"parsed": True, "content": "Sample structured data."}
    await db.parsed.update_one(
        {"filename": filename},
        {"$set": {"filename": filename, "parsed_content": parsed}},
        upsert=True
    )
    return ParsedResult(filename=filename, parsed_content=parsed)

# PUBLIC_INTERFACE
@router.get(
    "/parsed",
    summary="List all parsed files",
    description="List all parsed files and their parsed content.",
    response_model=List[ParsedResult],
)
async def list_parsed_files(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    List all parsed files stored in MongoDB.
    """
    cursor = db.parsed.find()
    result = []
    async for doc in cursor:
        result.append(ParsedResult(filename=doc["filename"], parsed_content=doc["parsed_content"]))
    return result
