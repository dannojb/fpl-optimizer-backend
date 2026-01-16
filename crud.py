"""
CRUD Operations

Database Create, Read, Update, Delete operations for FPL data.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from datetime import datetime


def get_player(db: Session, player_id: int) -> Optional[models.Player]:
    """
    Get a single player by ID.

    Args:
        db: Database session
        player_id: Player ID

    Returns:
        Player model or None if not found
    """
    return db.query(models.Player).filter(models.Player.id == player_id).first()


def get_players(db: Session, skip: int = 0, limit: int = 1000) -> List[models.Player]:
    """
    Get all players with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Player models
    """
    return db.query(models.Player).filter(models.Player.is_available == True).offset(skip).limit(limit).all()


def get_players_by_position(db: Session, position: int) -> List[models.Player]:
    """
    Get all players in a specific position.

    Args:
        db: Database session
        position: Position (1=GK, 2=DEF, 3=MID, 4=FWD)

    Returns:
        List of Player models
    """
    return db.query(models.Player).filter(
        models.Player.position == position,
        models.Player.is_available == True
    ).all()


def create_or_update_player(db: Session, player_data: dict) -> models.Player:
    """
    Create a new player or update existing player.

    Args:
        db: Database session
        player_data: Dictionary with player data

    Returns:
        Player model
    """
    existing_player = db.query(models.Player).filter(models.Player.id == player_data['id']).first()

    if existing_player:
        # Update existing player
        for key, value in player_data.items():
            setattr(existing_player, key, value)
        existing_player.last_updated = datetime.now()
        db.commit()
        db.refresh(existing_player)
        return existing_player
    else:
        # Create new player
        player = models.Player(**player_data)
        db.add(player)
        db.commit()
        db.refresh(player)
        return player


def bulk_create_or_update_players(db: Session, players_data: List[dict]) -> int:
    """
    Bulk create or update players.

    Args:
        db: Database session
        players_data: List of player dictionaries

    Returns:
        Number of players processed
    """
    count = 0
    for player_data in players_data:
        create_or_update_player(db, player_data)
        count += 1
    return count


def get_team(db: Session, team_id: int) -> Optional[models.Team]:
    """
    Get a single team by ID.

    Args:
        db: Database session
        team_id: Team ID

    Returns:
        Team model or None if not found
    """
    return db.query(models.Team).filter(models.Team.id == team_id).first()


def get_teams(db: Session) -> List[models.Team]:
    """
    Get all teams.

    Args:
        db: Database session

    Returns:
        List of Team models
    """
    return db.query(models.Team).all()


def create_or_update_team(db: Session, team_data: dict) -> models.Team:
    """
    Create a new team or update existing team.

    Args:
        db: Database session
        team_data: Dictionary with team data

    Returns:
        Team model
    """
    existing_team = db.query(models.Team).filter(models.Team.id == team_data['id']).first()

    if existing_team:
        # Update existing team
        for key, value in team_data.items():
            setattr(existing_team, key, value)
        existing_team.last_updated = datetime.now()
        db.commit()
        db.refresh(existing_team)
        return existing_team
    else:
        # Create new team
        team = models.Team(**team_data)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team


def get_current_gameweek(db: Session) -> Optional[models.Gameweek]:
    """
    Get the current gameweek.

    Args:
        db: Database session

    Returns:
        Gameweek model or None if not found
    """
    return db.query(models.Gameweek).filter(models.Gameweek.is_current == True).first()


def create_or_update_sync_metadata(
    db: Session,
    sync_type: str,
    status: str,
    records_synced: int = 0,
    error_message: Optional[str] = None
) -> models.SyncMetadata:
    """
    Create or update sync metadata.

    Args:
        db: Database session
        sync_type: Type of sync (e.g., 'bootstrap', 'fixtures')
        status: Sync status ('success' or 'failed')
        records_synced: Number of records synced
        error_message: Error message if sync failed

    Returns:
        SyncMetadata model
    """
    existing_metadata = db.query(models.SyncMetadata).filter(
        models.SyncMetadata.sync_type == sync_type
    ).first()

    metadata_data = {
        'sync_type': sync_type,
        'last_sync_time': datetime.now(),
        'last_sync_status': status,
        'records_synced': records_synced,
        'error_message': error_message
    }

    if existing_metadata:
        # Update existing metadata
        for key, value in metadata_data.items():
            setattr(existing_metadata, key, value)
        db.commit()
        db.refresh(existing_metadata)
        return existing_metadata
    else:
        # Create new metadata
        metadata = models.SyncMetadata(**metadata_data)
        db.add(metadata)
        db.commit()
        db.refresh(metadata)
        return metadata


def get_last_sync_time(db: Session, sync_type: str) -> Optional[datetime]:
    """
    Get the last successful sync time for a sync type.

    Args:
        db: Database session
        sync_type: Type of sync

    Returns:
        Datetime of last sync or None if never synced
    """
    metadata = db.query(models.SyncMetadata).filter(
        models.SyncMetadata.sync_type == sync_type,
        models.SyncMetadata.last_sync_status == 'success'
    ).first()

    return metadata.last_sync_time if metadata else None
