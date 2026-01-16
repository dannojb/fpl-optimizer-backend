"""
Data Sync Service

Synchronizes FPL data from API to local database.
"""

from sqlalchemy.orm import Session
from services.fpl_client import FPLClient
import crud
import logging
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)


class SyncService:
    """
    Service for synchronizing FPL API data to local database.

    Handles bootstrap data sync (players, teams, gameweeks).
    """

    def __init__(self, db: Session):
        self.db = db
        self.fpl_client = FPLClient()

    async def sync_bootstrap_data(self, force_refresh: bool = False) -> Tuple[bool, str]:
        """
        Sync all bootstrap data (players, teams, gameweeks) from FPL API.

        Args:
            force_refresh: Force refresh even if recently synced

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info("Starting bootstrap data sync")

            # Fetch bootstrap data from FPL API
            bootstrap = await self.fpl_client.get_bootstrap_static(force_refresh=force_refresh)

            if not bootstrap:
                error_msg = "Failed to fetch bootstrap data from FPL API"
                logger.error(error_msg)
                crud.create_or_update_sync_metadata(
                    self.db,
                    sync_type='bootstrap',
                    status='failed',
                    error_message=error_msg
                )
                return False, error_msg

            # Sync teams
            teams_synced = await self._sync_teams(bootstrap.get('teams', []))
            logger.info(f"Synced {teams_synced} teams")

            # Sync players
            players_synced = await self._sync_players(bootstrap.get('elements', []), bootstrap.get('teams', []))
            logger.info(f"Synced {players_synced} players")

            # Sync gameweeks
            gameweeks_synced = await self._sync_gameweeks(bootstrap.get('events', []))
            logger.info(f"Synced {gameweeks_synced} gameweeks")

            # Update sync metadata
            total_records = teams_synced + players_synced + gameweeks_synced
            crud.create_or_update_sync_metadata(
                self.db,
                sync_type='bootstrap',
                status='success',
                records_synced=total_records
            )

            success_msg = f"Bootstrap sync complete: {players_synced} players, {teams_synced} teams, {gameweeks_synced} gameweeks"
            logger.info(success_msg)
            return True, success_msg

        except Exception as e:
            error_msg = f"Error syncing bootstrap data: {str(e)}"
            logger.error(error_msg)
            crud.create_or_update_sync_metadata(
                self.db,
                sync_type='bootstrap',
                status='failed',
                error_message=error_msg
            )
            return False, error_msg

    async def _sync_teams(self, teams_data: list) -> int:
        """
        Sync teams data to database.

        Args:
            teams_data: List of team dictionaries from FPL API

        Returns:
            Number of teams synced
        """
        count = 0
        for team in teams_data:
            team_dict = {
                'id': team['id'],
                'name': team['name'],
                'short_name': team['short_name'],
                'code': team['code'],
                'strength': team.get('strength', 0),
                'strength_overall_home': team.get('strength_overall_home', 0),
                'strength_overall_away': team.get('strength_overall_away', 0),
                'strength_attack_home': team.get('strength_attack_home', 0),
                'strength_attack_away': team.get('strength_attack_away', 0),
                'strength_defence_home': team.get('strength_defence_home', 0),
                'strength_defence_away': team.get('strength_defence_away', 0),
            }
            crud.create_or_update_team(self.db, team_dict)
            count += 1

        return count

    async def _sync_players(self, players_data: list, teams_data: list) -> int:
        """
        Sync players data to database.

        Args:
            players_data: List of player dictionaries from FPL API
            teams_data: List of team dictionaries (for team name lookup)

        Returns:
            Number of players synced
        """
        # Create team ID to name mapping
        team_map = {team['id']: team['short_name'] for team in teams_data}

        count = 0
        for player in players_data:
            player_dict = {
                'id': player['id'],
                'web_name': player['web_name'],
                'first_name': player.get('first_name', ''),
                'second_name': player.get('second_name', ''),
                'position': player['element_type'],  # 1=GK, 2=DEF, 3=MID, 4=FWD
                'team_id': player['team'],
                'team_name': team_map.get(player['team'], 'Unknown'),
                'now_cost': player['now_cost'],
                'total_points': player['total_points'],
                'points_per_game': float(player.get('points_per_game', 0.0)),
                'form': float(player.get('form', 0.0)),
                'selected_by_percent': float(player.get('selected_by_percent', 0.0)),
                'minutes': player.get('minutes', 0),
                'goals_scored': player.get('goals_scored', 0),
                'assists': player.get('assists', 0),
                'clean_sheets': player.get('clean_sheets', 0),
                'bonus': player.get('bonus', 0),
                'influence': float(player.get('influence', 0.0)),
                'creativity': float(player.get('creativity', 0.0)),
                'threat': float(player.get('threat', 0.0)),
                'ict_index': float(player.get('ict_index', 0.0)),
                'is_available': player.get('status', 'a') == 'a',  # 'a' = available
            }
            crud.create_or_update_player(self.db, player_dict)
            count += 1

        return count

    async def _sync_gameweeks(self, gameweeks_data: list) -> int:
        """
        Sync gameweeks data to database.

        Args:
            gameweeks_data: List of gameweek/event dictionaries from FPL API

        Returns:
            Number of gameweeks synced
        """
        from models import Gameweek

        count = 0
        for event in gameweeks_data:
            # Check if gameweek exists
            existing = self.db.query(Gameweek).filter(Gameweek.id == event['id']).first()

            deadline_time = None
            if event.get('deadline_time'):
                try:
                    deadline_time = datetime.fromisoformat(event['deadline_time'].replace('Z', '+00:00'))
                except:
                    pass

            gameweek_data = {
                'name': event['name'],
                'deadline_time': deadline_time,
                'is_current': event.get('is_current', False),
                'is_next': event.get('is_next', False),
                'is_previous': event.get('is_previous', False),
                'finished': event.get('finished', False),
            }

            if existing:
                for key, value in gameweek_data.items():
                    setattr(existing, key, value)
                existing.last_updated = datetime.now()
            else:
                gameweek = Gameweek(id=event['id'], **gameweek_data)
                self.db.add(gameweek)

            count += 1

        self.db.commit()
        return count

    def should_sync(self, sync_type: str, max_age_hours: int = 6) -> bool:
        """
        Check if data should be re-synced based on last sync time.

        Args:
            sync_type: Type of sync (e.g., 'bootstrap')
            max_age_hours: Maximum age of data before re-sync (default: 6 hours)

        Returns:
            True if data should be synced, False otherwise
        """
        last_sync = crud.get_last_sync_time(self.db, sync_type)

        if not last_sync:
            return True  # Never synced

        age_hours = (datetime.now() - last_sync).total_seconds() / 3600
        return age_hours >= max_age_hours
