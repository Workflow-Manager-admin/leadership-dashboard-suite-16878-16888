from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

from src.api.routes.auth import get_current_active_user
from src.api.deps import get_db

router = APIRouter()


class UserRead(BaseModel):
    id: str = Field(..., example="660c6ade86941510f7dffb52")
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool

class TeamRead(BaseModel):
    id: str
    name: str
    description: Optional[str]

class ProjectRead(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: Optional[str]
    team_id: Optional[str]

# PUBLIC_INTERFACE
@router.get("/me", response_model=UserRead, summary="Get current user", tags=["User"])
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return UserRead(
        id=str(current_user["_id"]),
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        is_active=current_user.get("is_active", True),
        is_superuser=current_user.get("is_superuser", False),
    )

# PUBLIC_INTERFACE
@router.get("/teams", response_model=List[TeamRead], summary="List teams", tags=["User"])
async def list_teams(db=Depends(get_db), current_user=Depends(get_current_active_user)):
    teams = await db["teams"].find({}).to_list(length=100)
    return [
        TeamRead(
            id=str(team["_id"]),
            name=team["name"],
            description=team.get("description"),
        )
        for team in teams
    ]

# PUBLIC_INTERFACE
@router.get("/projects", response_model=List[ProjectRead], summary="List projects", tags=["User"])
async def list_projects(db=Depends(get_db), current_user=Depends(get_current_active_user)):
    projects = await db["projects"].find({}).to_list(length=100)
    return [
        ProjectRead(
            id=str(p["_id"]),
            name=p["name"],
            description=p.get("description"),
            owner_id=str(p["owner_id"]) if p.get("owner_id") else None,
            team_id=str(p["team_id"]) if p.get("team_id") else None,
        )
        for p in projects
    ]

# PUBLIC_INTERFACE
@router.get("/team/{team_id}", response_model=TeamRead, summary="Get team by id", tags=["User"])
async def get_team(team_id: str, db=Depends(get_db), current_user=Depends(get_current_active_user)):
    try:
        oid = ObjectId(team_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid team id")
    team = await db["teams"].find_one({"_id": oid})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamRead(
        id=str(team["_id"]),
        name=team["name"],
        description=team.get("description"),
    )

# PUBLIC_INTERFACE
@router.get("/project/{project_id}", response_model=ProjectRead, summary="Get project by id", tags=["User"])
async def get_project(project_id: str, db=Depends(get_db), current_user=Depends(get_current_active_user)):
    try:
        oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid project id")
    project = await db["projects"].find_one({"_id": oid})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead(
        id=str(project["_id"]),
        name=project["name"],
        description=project.get("description"),
        owner_id=str(project["owner_id"]) if project.get("owner_id") else None,
        team_id=str(project["team_id"]) if project.get("team_id") else None,
    )
