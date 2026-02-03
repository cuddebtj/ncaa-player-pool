"""
ESPN API service for fetching NCAA tournament data.
Provides methods to fetch tournaments, teams, players, and game statistics.
"""

from typing import Any

from .api_client import APIClient
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class ESPNService:
    """Service for interacting with ESPN's NCAA Basketball API."""

    # Known tournament ID for NCAA Men's Basketball Tournament
    NCAA_TOURNAMENT_ID = "56befd3f-4024-47c4-900f-892883cc1b6b"

    def __init__(self, config: Config, api_client: APIClient):
        """
        Initialize ESPN service.

        Args:
            config: Application configuration
            api_client: HTTP API client
        """
        self.config = config
        self.api_client = api_client
        self.data_dir = config.data_dir / "espn"

    async def fetch_tournament(
        self,
        tournament_id: str | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch NCAA tournament bracket and summary data.

        Args:
            tournament_id: Tournament ID (defaults to NCAA tournament)
            save: Whether to save response to file

        Returns:
            Tournament data dictionary
        """
        tournament_id = tournament_id or self.NCAA_TOURNAMENT_ID
        url = f"{self.config.espn_base_url}/tournaments/{tournament_id}/summary.json"

        save_to = None
        if save:
            save_to = self.data_dir / "tournaments" / f"tournament_{tournament_id}.json"

        logger.info(f"Fetching tournament data: {tournament_id}")
        data = await self.api_client.get(url, save_to=save_to)

        # Log tournament info
        if "name" in data:
            logger.info(f"Tournament: {data['name']}")
        if "brackets" in data:
            logger.info(f"Brackets found: {len(data['brackets'])}")

        return data

    async def fetch_team(
        self,
        team_id: str,
        save: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch team profile with roster and player information.

        Args:
            team_id: Team identifier
            save: Whether to save response to file

        Returns:
            Team data dictionary including roster
        """
        url = f"{self.config.espn_base_url}/teams/{team_id}"

        save_to = None
        if save:
            save_to = self.data_dir / "teams" / f"team_{team_id}.json"

        logger.info(f"Fetching team data: {team_id}")
        data = await self.api_client.get(url, save_to=save_to)

        # Log team info
        team_name = data.get("team", {}).get("displayName", "Unknown")
        logger.info(f"Team: {team_name}")

        return data

    async def fetch_team_roster(
        self,
        team_id: str,
        save: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch team roster with player information.

        Args:
            team_id: Team identifier
            save: Whether to save response to file

        Returns:
            Roster data dictionary with athletes
        """
        url = f"{self.config.espn_base_url}/teams/{team_id}/roster"

        save_to = None
        if save:
            save_to = self.data_dir / "teams" / f"team_{team_id}_roster.json"

        logger.info(f"Fetching roster data: {team_id}")
        data = await self.api_client.get(url, save_to=save_to)

        # Log roster info
        team_name = data.get("team", {}).get("displayName", "Unknown")
        athletes_count = len(data.get("athletes", []))
        logger.info(f"Team: {team_name} ({athletes_count} players)")

        return data

    async def fetch_teams_batch(
        self,
        team_ids: list[str],
        save: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Fetch multiple teams in batch.

        Args:
            team_ids: List of team identifiers
            save: Whether to save responses to files

        Returns:
            List of team data dictionaries
        """
        logger.info(f"Batch fetching {len(team_ids)} teams")

        urls = [f"{self.config.espn_base_url}/teams/{team_id}" for team_id in team_ids]

        save_dir = None
        if save:
            save_dir = self.data_dir / "teams"

        return await self.api_client.batch_get(urls, save_dir=save_dir, max_concurrent=3)

    async def fetch_rosters_batch(
        self,
        team_ids: list[str],
        save: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Fetch multiple team rosters in batch.

        Args:
            team_ids: List of team identifiers
            save: Whether to save responses to files

        Returns:
            List of roster data dictionaries
        """
        logger.info(f"Batch fetching rosters for {len(team_ids)} teams")

        urls = [f"{self.config.espn_base_url}/teams/{team_id}/roster" for team_id in team_ids]

        save_dir = None
        if save:
            save_dir = self.data_dir / "teams"

        return await self.api_client.batch_get(urls, save_dir=save_dir, max_concurrent=3)

    async def fetch_game_summary(
        self,
        game_id: str,
        save: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch game summary with box scores and player statistics.

        Args:
            game_id: Game/event identifier
            save: Whether to save response to file

        Returns:
            Game data dictionary with player stats
        """
        url = f"{self.config.espn_base_url}/summary?event={game_id}"

        save_to = None
        if save:
            save_to = self.data_dir / "games" / f"game_{game_id}.json"

        logger.info(f"Fetching game summary: {game_id}")
        data = await self.api_client.get(url, save_to=save_to)

        # Log game info
        if "header" in data:
            header = data["header"]
            teams = header.get("competitions", [{}])[0].get("competitors", [])
            if len(teams) >= 2:
                home = teams[0].get("team", {}).get("displayName", "Unknown")
                away = teams[1].get("team", {}).get("displayName", "Unknown")
                logger.info(f"Game: {away} vs {home}")

        return data

    async def fetch_games_batch(
        self,
        game_ids: list[str],
        save: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Fetch multiple games in batch.

        Args:
            game_ids: List of game identifiers
            save: Whether to save responses to files

        Returns:
            List of game data dictionaries
        """
        logger.info(f"Batch fetching {len(game_ids)} games")

        urls = [f"{self.config.espn_base_url}/summary?event={game_id}" for game_id in game_ids]

        save_dir = None
        if save:
            save_dir = self.data_dir / "games"

        return await self.api_client.batch_get(urls, save_dir=save_dir, max_concurrent=3)

    async def fetch_scoreboard(
        self,
        dates: str | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch current scoreboard for NCAA basketball.

        Args:
            dates: Optional date in format YYYYMMDD
            save: Whether to save response to file

        Returns:
            Scoreboard data with current/recent games
        """
        url = f"{self.config.espn_base_url}/scoreboard"

        params = {}
        if dates:
            params["dates"] = dates

        save_to = None
        if save:
            filename = f"scoreboard_{dates}.json" if dates else "scoreboard_current.json"
            save_to = self.data_dir / "tournaments" / filename

        logger.info("Fetching scoreboard")
        data = await self.api_client.get(url, params=params, save_to=save_to)

        # Log scoreboard info
        if "events" in data:
            logger.info(f"Games found: {len(data['events'])}")

        return data

    def extract_tournament_teams(self, tournament_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract team information from tournament data.

        Args:
            tournament_data: Tournament data from fetch_tournament()

        Returns:
            List of team dictionaries with id, name, seed
        """
        teams = []

        if "brackets" in tournament_data:
            for bracket in tournament_data["brackets"]:
                if "participants" in bracket:
                    for participant in bracket["participants"]:
                        team_info = {
                            "id": participant.get("id"),
                            "name": participant.get("displayName"),
                            "seed": participant.get("seed"),
                            "record": participant.get("record"),
                        }
                        teams.append(team_info)
                        logger.debug(f"Found team: {team_info['name']} (Seed {team_info['seed']})")

        logger.info(f"Extracted {len(teams)} teams from tournament data")
        return teams

    def extract_game_ids(self, tournament_data: dict[str, Any]) -> list[str]:
        """
        Extract all game IDs from tournament data.

        Args:
            tournament_data: Tournament data from fetch_tournament()

        Returns:
            List of game IDs
        """
        game_ids = []

        if "brackets" in tournament_data:
            for bracket in tournament_data["brackets"]:
                if "games" in bracket:
                    for game in bracket["games"]:
                        if "id" in game:
                            game_ids.append(game["id"])

        logger.info(f"Extracted {len(game_ids)} game IDs from tournament data")
        return game_ids
