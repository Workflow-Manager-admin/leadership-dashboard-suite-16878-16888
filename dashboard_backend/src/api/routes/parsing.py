from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from src.api.deps import get_db
import os

# Import parsers
import pandas as pd
from docx import Document as DocxDocument
from PyPDF2 import PdfReader
from pptx import Presentation

router = APIRouter()


class ParsedResult(BaseModel):
    filename: str
    parsed_content: dict


def parse_excel(path):
    try:
        df = pd.read_excel(path)
        return {"type": "excel", "columns": df.columns.tolist(), "rows": df.head(20).to_dict(orient="records")}
    except Exception as ex:
        return {"type": "excel", "error": str(ex)}


def parse_word(path):
    try:
        doc = DocxDocument(path)
        txt = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return {"type": "word", "content": txt}
    except Exception as ex:
        return {"type": "word", "error": str(ex)}


def parse_pdf(path):
    try:
        reader = PdfReader(path)
        text_pages = []
        for page in reader.pages[:10]:
            text_pages.append(page.extract_text())
        return {"type": "pdf", "pages": text_pages}
    except Exception as ex:
        return {"type": "pdf", "error": str(ex)}


def parse_ppt(path):
    try:
        pres = Presentation(path)
        slides = []
        for slide in pres.slides[:10]:
            tx = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    tx.append(shape.text)
            slides.append("\n".join(tx))
        return {"type": "ppt", "slides": slides}
    except Exception as ex:
        return {"type": "ppt", "error": str(ex)}


def guess_filetype(filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    if ext in ["xlsx", "xls"]:
        return "excel"
    if ext in ["docx", "doc"]:
        return "word"
    if ext in ["pdf"]:
        return "pdf"
    if ext in ["pptx", "ppt"]:
        return "ppt"
    return "unknown"


# PUBLIC_INTERFACE
@router.post(
    "/parse",
    summary="Parse a file",
    description="Trigger robust parsing of a previously uploaded file (Excel, Word, PDF, PPT).",
    response_model=ParsedResult)
async def parse_file(filename: str = Query(..., description="Filename of uploaded file to parse"), db=Depends(get_db)):
    upload_dir = "uploads"
    file_path = os.path.join(upload_dir, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found for parsing")
    kind = guess_filetype(filename)
    if kind == "excel":
        parsed = parse_excel(file_path)
    elif kind == "word":
        parsed = parse_word(file_path)
    elif kind == "pdf":
        parsed = parse_pdf(file_path)
    elif kind == "ppt":
        parsed = parse_ppt(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type for parsing")
    await db["parsed_results"].update_one(
        {"filename": filename},
        {"$set": {"parsed_content": parsed}},
        upsert=True,
    )
    return ParsedResult(filename=filename, parsed_content=parsed)
