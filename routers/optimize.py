"""
Optimization Router

API endpoints for generating transfer recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import logging
import time

from database import get_db
from schemas import OptimizationRequest, OptimizationResponse, PlayerBase, TransferRecommendation
from services.fpl_client import FPLClient
from services.sync_service import SyncService
from services.optimizer import optimizeTeam
import crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_team(
    request_body: OptimizationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate transfer recommendations for a team.

    Analyzes the current team and suggests 0-5 transfers to improve
    team performance based on form, points, and value.

    Args:
        request_body: Contains team_id

    Returns:
        OptimizationResponse with recommendations list and computation time

    Raises:
        404: Team not found
        503: FPL API unavailable or database not synced
    """
    team_id = request_body.team_id
    start_time = time.time()

    logger.info(f"Starting optimization for team {team_id}")

    # Initialize services
    fpl_client = FPLClient()
    sync_service = SyncService(db)

    # Ensure database is synced
    if sync_service.should_sync('bootstrap', max_age_hours=6):
        logger.info("Database is stale, syncing before optimization...")
        success, message = await sync_service.sync_bootstrap_data()
        if not success:
            logger.error(f"Sync failed: {message}")
            raise HTTPException(
                status_code=503,
                detail="Unable to sync player data from FPL API. Please try again later."
            )

    # Fetch team picks from FPL API
    picks_data = await fpl_client.get_team_picks(team_id)
    if not picks_data:
        raise HTTPException(
            status_code=404,
            detail=f"Team {team_id} not found or unable to fetch from FPL API."
        )

    # Get player IDs from picks
    player_ids = [pick['element'] for pick in picks_data['picks']]

    # Fetch current team players from database
    current_team = []
    for player_id in player_ids:
        player = crud.get_player(db, player_id)
        if player:
            current_team.append({
                'id': player.id,
                'web_name': player.web_name,
                'position': player.position,
                'team_name': player.team_name,
                'now_cost': player.now_cost,
                'total_points': player.total_points,
                'points_per_game': player.points_per_game,
                'form': player.form
            })

    if len(current_team) != 15:
        raise HTTPException(
            status_code=500,
            detail=f"Incomplete team data: expected 15 players, got {len(current_team)}"
        )

    # Fetch all available players from database
    all_players = crud.get_players(db, limit=1000)
    all_players_data = [{
        'id': p.id,
        'web_name': p.web_name,
        'position': p.position,
        'team_name': p.team_name,
        'now_cost': p.now_cost,
        'total_points': p.total_points,
        'points_per_game': p.points_per_game,
        'form': p.form
    } for p in all_players]

    logger.info(f"Running optimization: {len(current_team)} current players, {len(all_players_data)} candidates")

    # Run optimization algorithm
    result = optimizeTeam(current_team, all_players_data)

    # Convert result to response format
    recommendations = []
    for rec in result['recommendations']:
        recommendations.append(TransferRecommendation(
            playerOut=PlayerBase(**rec['playerOut']),
            playerIn=PlayerBase(**rec['playerIn']),
            rationale=rec['rationale'],
            cost_change=rec['cost_change']
        ))

    computation_time = (time.time() - start_time) * 1000  # Convert to milliseconds

    logger.info(f"Optimization complete: {len(recommendations)} recommendations in {computation_time:.0f}ms")

    return OptimizationResponse(
        recommendations=recommendations,
        computationTime=computation_time
    )
