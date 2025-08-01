"""
Manual tagging and rule definition APIs.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class Tag(BaseModel):
    tag_id: str
    name: str
    color: Optional[str]
    description: Optional[str]

class TagRule(BaseModel):
    rule_id: str
    rule_type: str
    definition: dict

TAGS = {}
RULES = {}

# PUBLIC_INTERFACE
@router.get("/tags", response_model=List[Tag])
def list_tags():
    return list(TAGS.values())

# PUBLIC_INTERFACE
@router.post("/tags", response_model=Tag)
def create_tag(tag: Tag):
    TAGS[tag.tag_id] = tag
    return tag

# PUBLIC_INTERFACE
@router.get("/rules", response_model=List[TagRule])
def list_rules():
    return list(RULES.values())

# PUBLIC_INTERFACE
@router.post("/rules", response_model=TagRule)
def create_rule(rule: TagRule):
    RULES[rule.rule_id] = rule
    return rule
