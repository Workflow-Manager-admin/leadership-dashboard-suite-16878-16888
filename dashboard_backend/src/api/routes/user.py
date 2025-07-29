from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.api.models_auth import User, Project, Team
from src.api.routes.auth import get_current_active_user
from src.api.deps import get_db

router = APIRouter()

# --- Schemas ---

class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool

    class Config:
        orm_mode = True

class TeamRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    class Config:
        orm_mode = True

class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    team_id: int
    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
@router.get("/me", response_model=UserRead, summary="Get current user", tags=["User"])
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# PUBLIC_INTERFACE
@router.get("/teams", response_model=List[TeamRead], summary="List teams", tags=["User"])
def list_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(Team).all()

# PUBLIC_INTERFACE
@router.get("/projects", response_model=List[ProjectRead], summary="List projects", tags=["User"])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(Project).all()

# PUBLIC_INTERFACE
@router.get("/team/{team_id}", response_model=TeamRead, summary="Get team by id", tags=["User"])
def get_team(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

# PUBLIC_INTERFACE
@router.get("/project/{project_id}", response_model=ProjectRead, summary="Get project by id", tags=["User"])
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
