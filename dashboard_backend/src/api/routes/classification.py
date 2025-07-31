from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import re
import uuid

from src.api.models import (
    ClassificationRuleEntity, RuleCreateEntity, RuleUpdateEntity,
    ClassificationResultEntity,
)

router = APIRouter()

# --- CRUD for Classification Rules ---

# PUBLIC_INTERFACE
@router.post(
    "/rules",
    summary="Create a rule",
    description="Add a new rule for document classification/tagging.",
    response_model=ClassificationRuleEntity,
    status_code=201,
)
async def create_rule(
    rule: RuleCreateEntity,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create and store a new rule for document classification/tagging."""
    rule_id = str(uuid.uuid4())
    rule_doc = {
        "rule_id": rule_id,
        "description": rule.description,
        "conditions": [cond.dict() for cond in rule.conditions],
        "tags": rule.tags
    }
    await db.classification_rules.insert_one(rule_doc)
    return ClassificationRuleEntity(**rule_doc)

# PUBLIC_INTERFACE
@router.get(
    "/rules",
    summary="List all rules",
    description="Retrieve all defined rules for classification/tagging",
    response_model=List[ClassificationRuleEntity]
)
async def list_rules(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """List all classification/tagging rules."""
    cursor = db.classification_rules.find()
    result = []
    async for doc in cursor:
        result.append(ClassificationRuleEntity(**doc))
    return result

# PUBLIC_INTERFACE
@router.get(
    "/rules/{rule_id}",
    summary="Get rule details",
    description="Retrieve a rule by its identifier",
    response_model=ClassificationRuleEntity
)
async def get_rule(
    rule_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Fetch rule details by rule_id."""
    doc = await db.classification_rules.find_one({"rule_id": rule_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    return ClassificationRuleEntity(**doc)

# PUBLIC_INTERFACE
@router.put(
    "/rules/{rule_id}",
    summary="Update a rule",
    description="Modify existing classification/tagging rule and replace relevant fields.",
    response_model=ClassificationRuleEntity,
)
async def update_rule(
    rule_id: str,
    update: RuleUpdateEntity,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update description/conditions/tags of the rule."""
    doc = await db.classification_rules.find_one({"rule_id": rule_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    update_data = {}
    if update.description is not None:
        update_data["description"] = update.description
    if update.conditions is not None:
        update_data["conditions"] = [c.dict() for c in update.conditions]
    if update.tags is not None:
        update_data["tags"] = update.tags
    if update_data:
        await db.classification_rules.update_one({"rule_id": rule_id}, {"$set": update_data})
    new_doc = await db.classification_rules.find_one({"rule_id": rule_id})
    return ClassificationRuleEntity(**new_doc)

# PUBLIC_INTERFACE
@router.delete(
    "/rules/{rule_id}",
    summary="Delete a rule",
    description="Remove a classification/tagging rule.",
    status_code=204,
)
async def delete_rule(
    rule_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete specified rule by rule_id."""
    res = await db.classification_rules.delete_one({"rule_id": rule_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


# --- Tagging/classification with rules ---

# PUBLIC_INTERFACE
@router.post(
    "/tag",
    summary="Apply manual tags or rules",
    description="Assign tags or classification rules to a parsed file. If `tags` omitted or empty, applies all rules to determine tags.",
    response_model=ClassificationResultEntity
)
async def tag_file(
    filename: str = Body(..., embed=True, description="Filename to classify/tag"),
    tags: Optional[List[str]] = Body(None, embed=True, description="Manual tags; if omitted or empty, rules will be applied for tag assignment."),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Assign provided tags, or if not supplied, apply classification/tagging rules to parsed file content.
    Stores tag result in `classification` collection.
    Returns tags applied.
    """
    if tags is not None and len(tags) > 0:
        tags_applied = tags
    else:
        # Find parsed content and apply rules
        parsed_doc = await db.parsed.find_one({"filename": filename})
        if not parsed_doc or "parsed_content" not in parsed_doc:
            raise HTTPException(status_code=404, detail=f"No parsed content found for {filename}")
        parsed_content = parsed_doc["parsed_content"]
        tags_applied = await _classify_by_rules(parsed_content, db)
    await db.classification.update_one(
        {"filename": filename},
        {"$set": {"filename": filename, "tags": tags_applied}},
        upsert=True
    )
    return ClassificationResultEntity(filename=filename, tags=tags_applied)


# PUBLIC_INTERFACE
@router.post(
    "/classify",
    summary="Reclassify using all rules",
    description="Evaluate all classification/tagging rules on a file's parsed content, and update its tags.",
    response_model=ClassificationResultEntity
)
async def classify_file_by_rules(
    filename: str = Body(..., embed=True, description="Filename to re-classify/tag"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Apply all classification/tagging rules to the file and replace the assigned tags.
    """
    parsed_doc = await db.parsed.find_one({"filename": filename})
    if not parsed_doc or "parsed_content" not in parsed_doc:
        raise HTTPException(status_code=404, detail=f"No parsed content found for {filename}")
    parsed_content = parsed_doc["parsed_content"]
    tags_applied = await _classify_by_rules(parsed_content, db)
    await db.classification.update_one(
        {"filename": filename},
        {"$set": {"filename": filename, "tags": tags_applied}},
        upsert=True
    )
    return ClassificationResultEntity(filename=filename, tags=tags_applied)


# PUBLIC_INTERFACE
@router.get(
    "/tags/{filename}",
    summary="Get tags/classification for file",
    description="Get the tags assigned (manually or by rules) for a given file.",
    response_model=ClassificationResultEntity
)
async def get_file_tags(
    filename: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Fetch document tags for a given filename."""
    doc = await db.classification.find_one({"filename": filename})
    if not doc:
        raise HTTPException(status_code=404, detail=f"No tags/classification for {filename}")
    return ClassificationResultEntity(filename=doc["filename"], tags=doc["tags"])


# --- Helper: rule-matching engine ---
async def _classify_by_rules(parsed_content, db: AsyncIOMotorDatabase):
    """
    Apply all rules in db.classification_rules to the provided parsed_content,
    collecting tags for any rule where all conditions are satisfied.
    """
    tags = set()
    cursor = db.classification_rules.find()
    async for rule in cursor:
        if _evaluate_rule_conditions(rule["conditions"], parsed_content):
            tags.update(rule["tags"])
    return list(sorted(tags))


def _evaluate_rule_conditions(conditions, parsed_content):
    """
    Return True if all specified conditions match parsed_content.
    Each condition: {field, op, value}
    """
    for cond in conditions:
        field_val = _extract_nested_value(parsed_content, cond["field"])
        op = cond["op"]
        target = cond["value"]
        if op == "equals":
            if field_val != target:
                return False
        elif op == "contains":
            if isinstance(field_val, str):
                if str(target) not in field_val:
                    return False
            elif isinstance(field_val, list):
                if target not in field_val:
                    return False
            else:
                return False
        elif op == "regex":
            if not isinstance(field_val, str):
                return False
            if not re.search(str(target), field_val):
                return False
        elif op == "gt":
            try:
                if not (field_val > target):
                    return False
            except Exception:
                return False
        elif op == "lt":
            try:
                if not (field_val < target):
                    return False
            except Exception:
                return False
        elif op == "in":
            if isinstance(target, list):
                if field_val not in target:
                    return False
            elif isinstance(field_val, list):
                if target not in field_val:
                    return False
            else:
                return False
        else:
            return False  # unsupported op
    return True


def _extract_nested_value(doc, dotfield):
    """
    Extract value from nested dict by dot-separated key.
    Returns None if not found.
    """
    keys = dotfield.split(".")
    val = doc
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return None
    return val

