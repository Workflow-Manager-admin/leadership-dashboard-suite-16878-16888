from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from src.api.deps import get_db
from src.api.routes.auth import get_current_active_user
from src.api.security import rate_limit

router = APIRouter()

class ClassificationInput(BaseModel):
    filename: str = Field(..., min_length=1, max_length=128, description="Filename to classify/tag")
    tags: List[str] = Field(..., min_items=1, max_items=50, description="Manual, auto, and rule-based tags")
    # Optionally features for advanced business logic
    rules: Optional[List[str]] = Field(default=None, description="Optional business rules to apply")
    overwrite: Optional[bool] = Field(default=True, description="Whether to overwrite or append tags")

class ClassificationResult(BaseModel):
    filename: str
    tags: List[str]

def content_based_tagging(db, filename, parsed_content) -> List[str]:
    # Demo: extract basic keywords; in real case: use NLP, regex, heuristics
    tags = []
    content = ""
    if isinstance(parsed_content, dict):
        if "columns" in parsed_content:  # Excel
            tags += list(parsed_content.get("columns", []))
        if "slides" in parsed_content:
            slides = parsed_content.get("slides", [])
            if slides: tags.append("slides")
        if "pages" in parsed_content:
            tags.append(f"{len(parsed_content.get('pages', []))}_pages")
        if "content" in parsed_content:
            content = parsed_content["content"]
    if isinstance(content, str):
        if "project" in content.lower(): tags.append("project")
        if "team" in content.lower(): tags.append("team")
        if "summary" in content.lower(): tags.append("summary")
    return [t.lower() for t in set(tags)]

# PUBLIC_INTERFACE
@router.post(
    "/tag",
    summary="Apply manual tags, rules, or advanced logic",
    description="Assign smart/manual tags or rules to a parsed file. Adds advanced business logic for classification.",
    response_model=ClassificationResult,
)
@rate_limit(10, 60)
async def apply_tags(
    request: Request,
    classification: ClassificationInput,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Load parsed content
    parsed_doc = await db["parsed_results"].find_one({"filename": classification.filename})
    if not parsed_doc:
        raise HTTPException(status_code=404, detail="Parsed data not found for classification.")
    # Smart (content-based) tags
    parsed_content = parsed_doc.get("parsed_content", {})
    smart_tags = content_based_tagging(db, classification.filename, parsed_content)
    tags_total = list(set(classification.tags + smart_tags))
    # Handle rules
    if classification.rules:
        # Example rule application
        for r in classification.rules:
            if r == "mark_summary" and "summary" not in tags_total:
                tags_total.append("summary")
    # Overwrite or append
    if classification.overwrite:
        await db["classification_tags"].delete_many({"filename": classification.filename})
    docs = [{"filename": classification.filename, "tag": tag} for tag in tags_total]
    if docs:
        await db["classification_tags"].insert_many(docs)
    return ClassificationResult(filename=classification.filename, tags=tags_total)
