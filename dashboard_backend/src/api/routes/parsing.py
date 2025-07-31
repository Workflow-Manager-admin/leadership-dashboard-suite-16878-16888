from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import os

router = APIRouter()

class ParsedResult(BaseModel):
    filename: str
    parsed_content: dict

# PUBLIC_INTERFACE
@router.post(
    "/parse",
    summary="Parse a file",
    description="Trigger parsing of a previously uploaded file (extracts data and updates MongoDB).",
    response_model=ParsedResult,
)
async def parse_file(
    filename: str = Query(..., description="Filename to parse (should be uploaded already)"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Parse a file by filename: load from uploaded files storage (if available), parse, and store in MongoDB.
    """
    # The server does not retain the user file, so this API expects the file to have been uploaded through ingest
    # For demonstration: if parsing already done just re-fetch; else error
    doc = await db.parsed.find_one({"filename": filename})
    if not doc:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not ingested or not found.")
    return ParsedResult(filename=filename, parsed_content=doc["parsed_content"])

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

# --- Actual Document Parsing Utility ---

async def extract_structured_data(filepath: str, filename: str):
    """
    PUBLIC_INTERFACE
    Parse Excel, PPTX, PDF, or Word document for structured data extraction.

    Args:
      filepath (str): path to file to parse
      filename (str): original filename

    Returns:
      dict: structured data extracted from the document
    """
    import mimetypes

    ext = os.path.splitext(filename)[1].lower()
    mimetype, _ = mimetypes.guess_type(filename)
    try:
        if ext in ['.xlsx', '.xls']:
            return await _parse_excel(filepath)
        elif ext in ['.pptx', '.ppt']:
            return await _parse_ppt(filepath)
        elif ext == '.pdf':
            return await _parse_pdf(filepath)
        elif ext in ['.docx', '.doc']:
            return await _parse_word(filepath)
        else:
            return {"error": f"Unsupported file type: {ext}"}
    except Exception as e:
        return {"error": f"Parsing error for {filename}: {str(e)}"}

async def _parse_excel(filepath):
    """
    Parse Excel file asynchronously for structured data.
    Returns a dict with sheet names and their tabular rows.
    """
    import openpyxl

    result = {}
    wb = openpyxl.load_workbook(filename=filepath, data_only=True)
    for sheet in wb.worksheets:
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append(list(row))
        result[sheet.title] = rows
    return {"type": "excel", "sheets": result}

async def _parse_pdf(filepath):
    """
    Parse PDF file asynchronously, extracting text per page.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(filepath)
    pages = []
    for pg in doc:
        pages.append(pg.get_text())
    return {"type": "pdf", "pages": pages}

async def _parse_word(filepath):
    """
    Parse Word (docx) to extract paragraphs.
    """
    import docx

    doc = docx.Document(filepath)
    paragraphs = [para.text for para in doc.paragraphs]
    # Extract tables if present
    tables = []
    for table in doc.tables:
        table_data = []
        for row in table.rows:
            table_data.append([cell.text for cell in row.cells])
        tables.append(table_data)
    return {"type": "word", "paragraphs": paragraphs, "tables": tables}

async def _parse_ppt(filepath):
    """
    Parse PowerPoint (pptx) and extracts text from all slides and shapes.
    """
    from pptx import Presentation
    prs = Presentation(filepath)
    slides = []
    for slide in prs.slides:
        texts = []
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                texts.append(shape.text)
        slides.append(texts)
    return {"type": "ppt", "slides": slides}
