"""
FPL API Client Service

Integrates with official Fantasy Premier League API to fetch player and team data.
"""

import httpx
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# FPL API base URL
FPL_API_BASE_URL = os.getenv("FPL_API_BASE_URL", "https://fantasy.premierleague.com/api")

# Cache for bootstrap data (reduce API calls)
_bootstrap_cache = None
_bootstrap_cache_time = None
CACHE_DURATION = timedelta(hours=6)  # Cache for 6 hours


class FPLClient:
    """
    Client for interacting with the official FPL API.

    Handles rate limiting, caching, and error handling.
    """

    def __init__(self):
        self.base_url = FPL_API_BASE_URL
        self.timeout = 10.0  # seconds

    async def get_bootstrap_static(self, force_refresh: bool = False) -> Optional[Dict]:
        """
        Fetch bootstrap-static data (all players, teams, gameweeks).

        This is the main endpoint containing all FPL data. It's cached for 6 hours
        to reduce API calls.

        Args:
            force_refresh: Force refresh cache even if still valid

        Returns:
            Dictionary with players, teams, events, etc. or None if error

        Example response structure:
        {
            "events": [...],      # Gameweeks
            "teams": [...],       # Premier League teams
            "elements": [...],    # All players
            "element_types": [...] # Position types
        }
        """
        global _bootstrap_cache, _bootstrap_cache_time

        # Return cached data if valid
        if not force_refresh and _bootstrap_cache and _bootstrap_cache_time:
            if datetime.now() - _bootstrap_cache_time < CACHE_DURATION:
                logger.info("Returning cached bootstrap data")
                return _bootstrap_cache

        # Fetch fresh data
        logger.info("Fetching fresh bootstrap data from FPL API")
        url = f"{self.base_url}/bootstrap-static/"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                _bootstrap_cache = data
                _bootstrap_cache_time = datetime.now()

                logger.info(f"Bootstrap data fetched: {len(data.get('elements', []))} players")
                return data

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching bootstrap data from {url}")
            # Return cached data if available
            return _bootstrap_cache if _bootstrap_cache else None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching bootstrap data: {e.response.status_code}")
            return _bootstrap_cache if _bootstrap_cache else None

        except Exception as e:
            logger.error(f"Unexpected error fetching bootstrap data: {str(e)}")
            return _bootstrap_cache if _bootstrap_cache else None

    async def get_team(self, team_id: int) -> Optional[Dict]:
        """
        Fetch user team data by team ID.

        Args:
            team_id: FPL team ID

        Returns:
            Dictionary with team information or None if error

        Example response structure:
        {
            "id": 123456,
            "name": "Team Name",
            "player_first_name": "John",
            "player_last_name": "Doe",
            "summary_overall_points": 1234,
            "summary_overall_rank": 12345,
            "current_event": 20,
            "leagues": {...}
        }
        """
        url = f"{self.base_url}/entry/{team_id}/"
        logger.info(f"Fetching team {team_id} from FPL API")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Team {team_id} fetched successfully")
                return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Team {team_id} not found")
            else:
                logger.error(f"HTTP error fetching team {team_id}: {e.response.status_code}")
            return None

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching team {team_id}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching team {team_id}: {str(e)}")
            return None

    async def get_team_picks(self, team_id: int, gameweek: Optional[int] = None) -> Optional[Dict]:
        """
        Fetch user's current team picks (15 players).

        Args:
            team_id: FPL team ID
            gameweek: Specific gameweek (if None, uses current gameweek)

        Returns:
            Dictionary with picks and automatic_subs or None if error

        Example response structure:
        {
            "active_chip": null,
            "automatic_subs": [],
            "entry_history": {...},
            "picks": [
                {
                    "element": 123,      # Player ID
                    "position": 1,       # Squad position (1-15)
                    "multiplier": 2,     # Captain/Vice-captain multiplier
                    "is_captain": true,
                    "is_vice_captain": false
                },
                ...
            ]
        }
        """
        # If no gameweek specified, get current gameweek from bootstrap
        if gameweek is None:
            bootstrap = await self.get_bootstrap_static()
            if not bootstrap:
                return None

            current_event = next((e for e in bootstrap['events'] if e['is_current']), None)
            gameweek = current_event['id'] if current_event else 1

        url = f"{self.base_url}/entry/{team_id}/event/{gameweek}/picks/"
        logger.info(f"Fetching team {team_id} picks for gameweek {gameweek}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Team {team_id} picks fetched: {len(data.get('picks', []))} players")
                return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Team {team_id} picks not found for gameweek {gameweek}")
            else:
                logger.error(f"HTTP error fetching team picks: {e.response.status_code}")
            return None

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching team {team_id} picks")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching team picks: {str(e)}")
            return None

    async def get_player_summary(self, player_id: int) -> Optional[Dict]:
        """
        Fetch detailed player summary including history and fixtures.

        Args:
            player_id: FPL player ID (element ID)

        Returns:
            Dictionary with history and fixtures or None if error

        Example response structure:
        {
            "fixtures": [...],     # Upcoming fixtures
            "history": [...],      # Past gameweek performance
            "history_past": [...]  # Previous seasons
        }
        """
        url = f"{self.base_url}/element-summary/{player_id}/"
        logger.info(f"Fetching player {player_id} summary")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Player {player_id} summary fetched")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching player {player_id} summary: {e.response.status_code}")
            return None

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching player {player_id} summary")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching player summary: {str(e)}")
            return None

    async def get_fixtures(self, gameweek: Optional[int] = None) -> Optional[List[Dict]]:
        """
        Fetch fixtures for a specific gameweek or all fixtures.

        Args:
            gameweek: Specific gameweek (if None, returns all fixtures)

        Returns:
            List of fixture dictionaries or None if error

        Example fixture structure:
        {
            "code": 123456,
            "event": 20,              # Gameweek
            "finished": false,
            "team_h": 1,              # Home team ID
            "team_a": 2,              # Away team ID
            "team_h_difficulty": 3,   # Difficulty rating (1-5)
            "team_a_difficulty": 2
        }
        """
        url = f"{self.base_url}/fixtures/"
        if gameweek:
            url += f"?event={gameweek}"

        logger.info(f"Fetching fixtures" + (f" for gameweek {gameweek}" if gameweek else ""))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Fixtures fetched: {len(data)} fixtures")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching fixtures: {e.response.status_code}")
            return None

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching fixtures")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching fixtures: {str(e)}")
            return None

    def clear_cache(self):
        """Clear the bootstrap data cache."""
        global _bootstrap_cache, _bootstrap_cache_time
        _bootstrap_cache = None
        _bootstrap_cache_time = None
        logger.info("Bootstrap cache cleared")
