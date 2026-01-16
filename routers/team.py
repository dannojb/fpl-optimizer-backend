"""
Team Router

API endpoints for fetching FPL team data.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import logging

from database import get_db
from schemas import TeamResponse, PlayerBase, ErrorResponse
from services.fpl_client import FPLClient
from services.sync_service import SyncService
import crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/team/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Fetch FPL team data by team ID.

    Returns the user's current 15-player squad with real data from FPL API.

    Args:
        team_id: FPL team ID (from user's profile URL)

    Returns:
        TeamResponse with players list and team statistics

    Raises:
        404: Team not found
        503: FPL API unavailable
    """
    logger.info(f"Fetching team {team_id}")

    # Initialize services
    fpl_client = FPLClient()
    sync_service = SyncService(db)

    # Sync data if needed (checks last sync time internally)
    if sync_service.should_sync('bootstrap', max_age_hours=6):
        logger.info("Bootstrap data is stale, syncing...")
        success, message = await sync_service.sync_bootstrap_data()
        if not success:
            logger.warning(f"Sync failed but continuing with cached data: {message}")

    # Fetch team data from FPL API
    team_data = await fpl_client.get_team(team_id)
    if not team_data:
        raise HTTPException(
            status_code=404,
            detail=f"Team {team_id} not found. Please check your FPL team ID."
        )

    # Fetch team picks (current squad)
    picks_data = await fpl_client.get_team_picks(team_id)
    if not picks_data:
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch team picks from FPL API. Please try again later."
        )

    # Get player IDs from picks
    player_ids = [pick['element'] for pick in picks_data['picks']]

    # Fetch player data from database
    players = []
    for player_id in player_ids:
        player = crud.get_player(db, player_id)
        if player:
            players.append(PlayerBase(
                id=player.id,
                web_name=player.web_name,
                position=player.position,
                team_name=player.team_name,
                now_cost=player.now_cost,
                total_points=player.total_points,
                points_per_game=player.points_per_game,
                form=player.form
            ))
        else:
            # Player not in database - this shouldn't happen after sync
            logger.warning(f"Player {player_id} not found in database")

    if len(players) != 15:
        logger.error(f"Expected 15 players but got {len(players)}")
        raise HTTPException(
            status_code=500,
            detail="Incomplete team data. Please try again."
        )

    # Calculate team value and total points
    team_value = sum(p.now_cost for p in players) / 10.0  # Convert to millions
    total_points = sum(p.total_points for p in players)

    logger.info(f"Team {team_id} fetched successfully: {len(players)} players, £{team_value:.1f}m value")

    return TeamResponse(
        team_id=team_id,
        players=players,
        team_value=team_value,
        total_points=total_points
    )
