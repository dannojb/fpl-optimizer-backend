"""
Database Models

SQLAlchemy ORM models for FPL data storage.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from database import Base


class Player(Base):
    """
    Player model - stores FPL player data from bootstrap-static API.
    """
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    web_name = Column(String, nullable=False, index=True)
    first_name = Column(String)
    second_name = Column(String)
    position = Column(Integer, nullable=False)  # 1=GK, 2=DEF, 3=MID, 4=FWD
    team_name = Column(String, nullable=False, index=True)
    team_id = Column(Integer, nullable=False)
    now_cost = Column(Integer, nullable=False)  # Cost in tenths (e.g., 85 = £8.5m)
    total_points = Column(Integer, default=0)
    points_per_game = Column(Float, default=0.0)
    form = Column(Float, default=0.0)
    selected_by_percent = Column(Float, default=0.0)
    minutes = Column(Integer, default=0)
    goals_scored = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    clean_sheets = Column(Integer, default=0)
    bonus = Column(Integer, default=0)
    influence = Column(Float, default=0.0)
    creativity = Column(Float, default=0.0)
    threat = Column(Float, default=0.0)
    ict_index = Column(Float, default=0.0)

    # Metadata
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_available = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Player {self.web_name} ({self.team_name})>"


class Team(Base):
    """
    Team model - stores Premier League team information.
    """
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    code = Column(Integer, unique=True)
    strength = Column(Integer, default=0)
    strength_overall_home = Column(Integer, default=0)
    strength_overall_away = Column(Integer, default=0)
    strength_attack_home = Column(Integer, default=0)
    strength_attack_away = Column(Integer, default=0)
    strength_defence_home = Column(Integer, default=0)
    strength_defence_away = Column(Integer, default=0)

    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Team {self.name}>"


class Gameweek(Base):
    """
    Gameweek model - stores gameweek/event information.
    """
    __tablename__ = "gameweeks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    deadline_time = Column(DateTime)
    is_current = Column(Boolean, default=False)
    is_next = Column(Boolean, default=False)
    is_previous = Column(Boolean, default=False)
    finished = Column(Boolean, default=False)

    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Gameweek {self.name}>"


class SyncMetadata(Base):
    """
    Sync metadata model - tracks last successful data sync from FPL API.
    """
    __tablename__ = "sync_metadata"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String, nullable=False, unique=True)  # 'bootstrap', 'fixtures', etc.
    last_sync_time = Column(DateTime, nullable=False)
    last_sync_status = Column(String, nullable=False)  # 'success', 'failed'
    error_message = Column(Text, nullable=True)
    records_synced = Column(Integer, default=0)

    def __repr__(self):
        return f"<SyncMetadata {self.sync_type}: {self.last_sync_status}>"
