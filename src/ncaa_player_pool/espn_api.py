"""ESPN API integration for NCAA basketball data.

This module provides a high-level service for interacting with ESPN's
public NCAA Basketball API. It handles fetching tournament brackets,
team rosters, game summaries, and scoreboards.

Example:
    Basic usage for fetching tournament data::

        from ncaa_player_pool.espn_api import ESPNService
        from ncaa_player_pool.api_client import APIClient
        from ncaa_player_pool.config import get_config

        config = get_config()

        async with APIClient(config) as client:
            espn = ESPNService(config, client)

            # Fetch tournament bracket
            tournament = await espn.fetch_tournament()

            # Extract team IDs and fetch rosters
            team_ids = [team["id"] for team in espn.extract_tournament_teams(tournament)]
            rosters = await espn.fetch_rosters_batch(team_ids)

Attributes:
    logger: Module-level logger for ESPN API operations.

Note:
    ESPN's API is undocumented and may change without notice. This module
    is designed to handle common response formats but may need updates
    if ESPN modifies their API structure.
"""

from typing import Any

from .api_client import APIClient
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class ESPNService:
    """High-level service for ESPN NCAA Basketball API interactions.

    Provides methods to fetch tournament data, team rosters, game summaries,
    and scoreboards from ESPN's API. Handles URL construction, response
    saving, and basic data extraction.

    Attributes:
        NCAA_TOURNAMENT_ID: Default tournament ID for NCAA Men's Basketball
            March Madness tournament.
        config: Application configuration instance.
        api_client: HTTP client for making API requests.
        data_dir: Directory path for saving API responses.

    Example:
        Fetch and process tournament data::

            async with APIClient(config) as client:
                espn = ESPNService(config, client)

                # Fetch tournament bracket
                tournament = await espn.fetch_tournament()

                # Get all team info
                teams = espn.extract_tournament_teams(tournament)
                print(f"Found {len(teams)} teams")

                # Fetch game summaries
                game_ids = espn.extract_game_ids(tournament)
                summaries = await espn.fetch_games_batch(game_ids)
    """

    # Known tournament ID for NCAA Men's Basketball Tournament
    NCAA_TOURNAMENT_ID = "56befd3f-4024-47c4-900f-892883cc1b6b"

    def __init__(self, config: Config, api_client: APIClient):
        """Initialize ESPN service with configuration and HTTP client.

        Args:
            config: Application configuration containing ESPN base URL
                and data directory settings.
            api_client: Initialized HTTP API client for making requests.
        """
        self.config = config
        self.api_client = api_client
        self.data_dir = config.data_dir / "espn"

    async def fetch_tournament(
        self,
        tournament_id: str | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        """Fetch NCAA tournament bracket and summary data.

        Retrieves the tournament structure including brackets, seeds,
        participants, and game schedules.

        Args:
            tournament_id: ESPN tournament identifier. Defaults to
                NCAA_TOURNAMENT_ID (March Madness).
            save: If True, saves the response JSON to the data directory.

        Returns:
            Tournament data dictionary containing brackets, participants,
            and game information.

        Note:
            Tournament bracket data is only available during March Madness.
            Outside this period, the API may return limited or no data.
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
        """Fetch team profile with basic information.

        Retrieves team details including name, location, conference,
        and basic statistics.

        Args:
            team_id: ESPN team identifier (numeric string).
            save: If True, saves the response JSON to data/espn/teams/.

        Returns:
            Team data dictionary containing team profile information.
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
        """Fetch team roster with player details.

        Retrieves the complete roster including player names, positions,
        jersey numbers, and other biographical information.

        Args:
            team_id: ESPN team identifier (numeric string).
            save: If True, saves the response JSON to data/espn/teams/.

        Returns:
            Roster data dictionary containing team info and athletes list.
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
        """Fetch multiple team profiles concurrently.

        Uses the API client's batch_get method to fetch multiple teams
        with controlled concurrency.

        Args:
            team_ids: List of ESPN team identifiers.
            save: If True, saves responses to data/espn/teams/.

        Returns:
            List of team data dictionaries. Failed fetches are excluded.
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
        """Fetch multiple team rosters concurrently.

        Uses the API client's batch_get method to fetch multiple rosters
        with controlled concurrency. Useful for fetching all tournament
        team rosters at once.

        Args:
            team_ids: List of ESPN team identifiers.
            save: If True, saves responses to data/espn/teams/.

        Returns:
            List of roster data dictionaries. Failed fetches are excluded.
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
        """Fetch detailed game summary with box scores.

        Retrieves complete game information including final scores,
        player statistics, play-by-play data, and game header info.

        Args:
            game_id: ESPN game/event identifier (numeric string).
            save: If True, saves response to data/espn/games/.

        Returns:
            Game summary dictionary containing header, boxscore,
            and player statistics.
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
        """Fetch multiple game summaries concurrently.

        Uses the API client's batch_get method to fetch multiple game
        summaries with controlled concurrency.

        Args:
            game_ids: List of ESPN game/event identifiers.
            save: If True, saves responses to data/espn/games/.

        Returns:
            List of game summary dictionaries. Failed fetches are excluded.
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
        """Fetch NCAA basketball scoreboard with game listings.

        Retrieves current or historical game listings including scores,
        game status, and participating teams.

        Args:
            dates: Optional date filter in YYYYMMDD format (e.g., "20260319").
                If not provided, returns current/recent games.
            save: If True, saves response to data/espn/tournaments/.

        Returns:
            Scoreboard data containing events list with game information.

        Example:
            Fetch games for a specific date::

                scoreboard = await espn.fetch_scoreboard(dates="20260319")
                for event in scoreboard["events"]:
                    print(event["name"])
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
        """Extract team information from tournament bracket data.

        Parses tournament response to extract all participating teams
        with their seeds and records.

        Args:
            tournament_data: Raw tournament data from fetch_tournament().

        Returns:
            List of team dictionaries, each containing:
                - id: Team identifier
                - name: Team display name
                - seed: Tournament seed (1-16)
                - record: Team's season record

        Example:
            Get all tournament teams::

                tournament = await espn.fetch_tournament()
                teams = espn.extract_tournament_teams(tournament)
                for team in teams:
                    print(f"#{team['seed']} {team['name']}")
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
        """Extract all game IDs from tournament bracket data.

        Parses tournament response to get all scheduled and completed
        game identifiers, which can be used to fetch game summaries.

        Args:
            tournament_data: Raw tournament data from fetch_tournament().

        Returns:
            List of game ID strings for all tournament games.

        Example:
            Fetch all tournament game summaries::

                tournament = await espn.fetch_tournament()
                game_ids = espn.extract_game_ids(tournament)
                summaries = await espn.fetch_games_batch(game_ids)
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
