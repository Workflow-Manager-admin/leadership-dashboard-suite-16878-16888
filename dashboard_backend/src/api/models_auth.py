"""
ORM models for authentication, user, team, and project.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base

# Association table for User-Team relationship (many-to-many)
user_team_association = Table(
    'user_team',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('team_id', Integer, ForeignKey('teams.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teams = relationship('Team', secondary=user_team_association, back_populates='users')
    projects = relationship('Project', back_populates='owner', lazy='dynamic')

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)

    users = relationship('User', secondary=user_team_association, back_populates='teams')
    projects = relationship('Project', back_populates='team', lazy='dynamic')

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship('User', back_populates="projects")
    team = relationship('Team', back_populates="projects")
