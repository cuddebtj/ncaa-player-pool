"""Google Sheets integration for NCAA Player Pool.

This module provides functionality to export player rosters and game
statistics to Google Sheets. It uses gspread with service account
authentication for API access.

Prerequisites:
    1. Create a Google Cloud project and enable Sheets API
    2. Create a service account and download JSON credentials
    3. Share your spreadsheet with the service account email
    4. Set GOOGLE_CREDENTIALS_FILE and GOOGLE_SHEET_ID in environment

Example:
    Export all data to Google Sheets::

        from ncaa_player_pool.sheets import export_all_data
        from ncaa_player_pool.config import get_config

        config = get_config()
        url = export_all_data(config, year=2026)
        print(f"Data exported to: {url}")

    Manual export with custom sheets::

        from ncaa_player_pool.sheets import SheetsClient
        from ncaa_player_pool.config import get_config

        config = get_config()
        sheets = SheetsClient(config)
        sheets.authenticate()
        sheets.open_spreadsheet()

        sheets.export_players(players_data, worksheet_name="My Roster")
        sheets.export_player_stats(stats_data, worksheet_name="My Stats")

Attributes:
    logger: Module-level logger for Google Sheets operations.

Classes:
    SheetsClient: Client for Google Sheets API operations.

Functions:
    export_all_data: High-level function to export all data at once.
"""

from pathlib import Path
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class SheetsClient:
    """Google Sheets client for exporting NCAA pool data.

    Provides methods to authenticate with Google Sheets API, open
    spreadsheets, and export player/stats data with formatting.

    Attributes:
        SCOPES: Required Google API scopes for Sheets and Drive access.
        config: Application configuration instance.
        client: Authenticated gspread client, or None if not authenticated.
        spreadsheet: Currently open spreadsheet, or None if not opened.

    Example:
        Export players to a sheet::

            sheets = SheetsClient(config)
            sheets.authenticate()
            sheets.open_spreadsheet("your-spreadsheet-id")
            sheets.export_players(players_data)
    """

    # Google Sheets API scopes
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    def __init__(self, config: Config):
        """Initialize Google Sheets client with configuration.

        Args:
            config: Application configuration containing Google credentials
                file path and sheet ID settings.
        """
        self.config = config
        self.client: gspread.Client | None = None
        self.spreadsheet: gspread.Spreadsheet | None = None

    def authenticate(self) -> None:
        """Authenticate with Google Sheets API using service account.

        Reads credentials from the JSON file specified in configuration
        and creates an authenticated gspread client.

        Raises:
            ValueError: If GOOGLE_CREDENTIALS_FILE is not set.
            FileNotFoundError: If credentials file doesn't exist.
            Exception: If authentication fails for other reasons.

        Example:
            Authenticate before using other methods::

                sheets = SheetsClient(config)
                sheets.authenticate()
                # Now ready to open spreadsheets
        """
        if not self.config.google_credentials_file:
            raise ValueError("GOOGLE_CREDENTIALS_FILE not set in environment")

        creds_path = Path(self.config.google_credentials_file)
        if not creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found: {creds_path}")

        try:
            credentials = Credentials.from_service_account_file(str(creds_path), scopes=self.SCOPES)
            self.client = gspread.authorize(credentials)
            logger.info("Successfully authenticated with Google Sheets API")

        except Exception as e:
            logger.exception(f"Failed to authenticate with Google Sheets: {e}")
            raise

    def open_spreadsheet(self, sheet_id: str | None = None) -> None:
        """Open a Google Spreadsheet by ID.

        Opens the specified spreadsheet and stores it for subsequent
        operations. Automatically authenticates if not already done.

        Args:
            sheet_id: Google Spreadsheet ID (from the URL). If not provided,
                uses GOOGLE_SHEET_ID from configuration.

        Raises:
            ValueError: If sheet_id is not provided and not in config.
            gspread.SpreadsheetNotFound: If spreadsheet doesn't exist.
            gspread.exceptions.APIError: If access is denied.

        Example:
            Open spreadsheet from URL ID::

                # URL: https://docs.google.com/spreadsheets/d/ABC123/edit
                sheets.open_spreadsheet("ABC123")
        """
        if not self.client:
            self.authenticate()

        sheet_id = sheet_id or self.config.google_sheet_id
        if not sheet_id:
            raise ValueError("Google Sheet ID not provided and not in config")

        try:
            self.spreadsheet = self.client.open_by_key(sheet_id)
            logger.info(f"Opened spreadsheet: {self.spreadsheet.title}")

        except Exception as e:
            logger.exception(f"Failed to open spreadsheet {sheet_id}: {e}")
            raise

    def get_or_create_worksheet(self, title: str, rows: int = 1000, cols: int = 26) -> gspread.Worksheet:
        """Get existing worksheet or create a new one.

        Attempts to find a worksheet with the given title. If not found,
        creates a new worksheet with the specified dimensions.

        Args:
            title: Worksheet/tab name to find or create.
            rows: Number of rows for new worksheet (default 1000).
            cols: Number of columns for new worksheet (default 26, A-Z).

        Returns:
            The existing or newly created worksheet object.

        Raises:
            ValueError: If no spreadsheet is currently open.

        Example:
            Get or create a stats worksheet::

                ws = sheets.get_or_create_worksheet("Player Stats", rows=5000)
                ws.update_cell(1, 1, "Player ID")
        """
        if not self.spreadsheet:
            raise ValueError("No spreadsheet opened. Call open_spreadsheet() first")

        try:
            worksheet = self.spreadsheet.worksheet(title)
            logger.info(f"Found existing worksheet: {title}")
            return worksheet

        except gspread.WorksheetNotFound:
            logger.info(f"Creating new worksheet: {title}")
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)
            return worksheet

    def export_players(self, players_data: list[dict[str, Any]], worksheet_name: str = "Players") -> None:
        """Export tournament player roster to Google Sheets.

        Creates/updates a worksheet with player roster information including
        player ID, name, position, team, and seed. Applies formatting with
        a styled header row and frozen headers.

        Sheet columns:
            - Player ID: ESPN player identifier
            - Player Name: Full player name
            - Position: Player position (G, F, C, etc.)
            - Team: Team name
            - Team Seed: Tournament seed (1-16)
            - Player Team: Combined player/team identifier

        Args:
            players_data: List of player dictionaries from database export,
                each containing player_id, player_name, position, team_name,
                seed, and player_team keys.
            worksheet_name: Name of the worksheet/tab to create or update.

        Raises:
            ValueError: If no spreadsheet is currently open.

        Example:
            Export roster to Players sheet::

                players = db.get_players_export(2026)
                sheets.export_players(players)
        """
        if not self.spreadsheet:
            raise ValueError("No spreadsheet opened. Call open_spreadsheet() first")

        logger.info(f"Exporting {len(players_data)} players to '{worksheet_name}' worksheet")

        # Get or create worksheet
        worksheet = self.get_or_create_worksheet(worksheet_name)

        # Clear existing data
        worksheet.clear()

        if not players_data:
            logger.warning("No player data to export")
            return

        # Prepare header row
        headers = [
            "Player ID",
            "Player Name",
            "Position",
            "Team",
            "Team Seed",
            "Player Team",
        ]

        # Prepare data rows
        rows = [headers]
        for player in players_data:
            row = [
                player.get("player_id", ""),
                player.get("player_name", ""),
                player.get("position", ""),
                player.get("team_name", ""),
                player.get("seed") if player.get("seed") is not None else "",
                player.get("player_team", ""),
            ]
            rows.append(row)

        # Write to sheet
        worksheet.update(rows, value_input_option="RAW")

        # Format header row
        worksheet.format(
            "A1:F1",
            {
                "backgroundColor": {"red": 0.2, "green": 0.5, "blue": 0.8},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "horizontalAlignment": "CENTER",
            },
        )

        # Freeze header row
        worksheet.freeze(rows=1)

        logger.info(f"Successfully exported {len(players_data)} players")

    def export_player_stats(self, stats_data: list[dict[str, Any]], worksheet_name: str = "Player Stats") -> None:
        """Export detailed player game statistics to Google Sheets.

        Creates/updates a worksheet with per-game player statistics including
        all box score data. Applies formatting with styled headers, number
        formatting for stats columns, and frozen headers.

        Sheet columns:
            - Player ID: ESPN player identifier
            - Is Eliminated: Whether player's team is eliminated
            - Player Name: Full player name
            - Position: Player position
            - Team: Team name
            - Team Seed: Tournament seed
            - Game ID: ESPN game identifier
            - Round: Tournament round name
            - Home Team: Home team name
            - Away Team: Away team name
            - Game Date: Scheduled game date
            - Points, Assists, Rebounds, Steals, Blocks, Turnovers, Fouls
            - Minutes Played: Total minutes in game
            - Total Score: PTS + AST + REB

        Args:
            stats_data: List of game stats dictionaries from database export,
                each containing player info, game info, and all statistics.
            worksheet_name: Name of the worksheet/tab to create or update.

        Raises:
            ValueError: If no spreadsheet is currently open.

        Example:
            Export game-by-game stats::

                stats = db.get_game_stats_export(2026)
                sheets.export_player_stats(stats)
        """
        if not self.spreadsheet:
            raise ValueError("No spreadsheet opened. Call open_spreadsheet() first")

        logger.info(f"Exporting {len(stats_data)} stat records to '{worksheet_name}' worksheet")

        # Get or create worksheet
        worksheet = self.get_or_create_worksheet(worksheet_name, rows=5000, cols=20)

        # Clear existing data
        worksheet.clear()

        if not stats_data:
            logger.warning("No stats data to export")
            return

        # Prepare header row
        headers = [
            "Player ID",
            "Is Eliminated",
            "Player Name",
            "Position",
            "Team",
            "Team Seed",
            "Game ID",
            "Round",
            "Home Team",
            "Away Team",
            "Game Date",
            "Points",
            "Assists",
            "Rebounds",
            "Steals",
            "Blocks",
            "Turnovers",
            "Fouls",
            "Minutes Played",
            "Total Score (PTS+AST+REB)",
        ]

        # Prepare data rows
        rows = [headers]
        for stats in stats_data:
            row = [
                stats.get("player_id", ""),
                "Yes" if stats.get("eliminated") else "No",
                stats.get("player_name", ""),
                stats.get("position", ""),
                stats.get("player_team", ""),
                stats.get("seed") if stats.get("seed") is not None else "",
                stats.get("game_id", ""),
                stats.get("round_name", ""),
                stats.get("home_team", ""),
                stats.get("away_team", ""),
                str(stats.get("scheduled_date", "")) if stats.get("scheduled_date") else "",
                stats.get("points", 0),
                stats.get("assists", 0),
                stats.get("rebounds", 0),
                stats.get("steals", 0),
                stats.get("blocks", 0),
                stats.get("turnovers", 0),
                stats.get("fouls", 0),
                stats.get("minutes_played", 0) if stats.get("minutes_played") is not None else "",
                stats.get("total_score", 0),
            ]
            rows.append(row)

        # Write to sheet
        worksheet.update(rows, value_input_option="RAW")

        # Format header row
        worksheet.format(
            "A1:T1",
            {
                "backgroundColor": {"red": 0.2, "green": 0.5, "blue": 0.8},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "horizontalAlignment": "CENTER",
                "wrapStrategy": "WRAP",
            },
        )

        # Format eliminated column with conditional colors
        # Green for No (active), Red for Yes (eliminated)
        worksheet.format("B2:B5000", {"horizontalAlignment": "CENTER"})

        # Format stat columns as numbers
        stat_cols = ["L", "M", "N", "O", "P", "Q", "R", "S", "T"]  # Points through Total Score
        for col in stat_cols:
            worksheet.format(
                f"{col}2:{col}5000",
                {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}},
            )

        # Bold and highlight total score column
        worksheet.format("T2:T5000", {"textFormat": {"bold": True}})

        # Freeze header row
        worksheet.freeze(rows=1)

        logger.info(f"Successfully exported {len(stats_data)} stat records")


def export_all_data(config: Config, year: int, sheet_id: str | None = None) -> str:
    """Export all tournament data to Google Sheets.

    High-level convenience function that exports both the player roster
    and game-by-game statistics to a Google Spreadsheet. Creates two
    worksheets: "Players" and "Player Stats".

    This function handles the complete workflow:
    1. Initialize and authenticate Sheets client
    2. Open the target spreadsheet
    3. Query database for player and stats data
    4. Export both datasets with formatting

    Args:
        config: Application configuration with database and Google
            credentials settings.
        year: Tournament year to export data for.
        sheet_id: Google Spreadsheet ID. If not provided, uses
            GOOGLE_SHEET_ID from configuration.

    Returns:
        URL of the updated Google Spreadsheet.

    Raises:
        ValueError: If Google credentials or sheet ID not configured.
        FileNotFoundError: If credentials file doesn't exist.
        psycopg.DatabaseError: If database connection fails.

    Example:
        Export 2026 tournament data::

            from ncaa_player_pool.sheets import export_all_data
            from ncaa_player_pool.config import get_config

            config = get_config()
            url = export_all_data(config, 2026)
            print(f"View results at: {url}")
    """
    from .db import Database

    logger.info(f"Starting full export for year {year}")

    # Initialize sheets client
    sheets = SheetsClient(config)
    sheets.authenticate()
    sheets.open_spreadsheet(sheet_id)

    # Get data from database
    with Database(config) as db:
        # Get players for roster
        players_data = db.get_players_export(year)

        # Get detailed game-by-game stats
        stats_data = db.get_game_stats_export(year)

    # Export to sheets
    sheets.export_players(players_data, worksheet_name="Players")
    sheets.export_player_stats(stats_data, worksheet_name="Player Stats")

    logger.info(f"Successfully exported all data for year {year}")
    logger.info(f"Spreadsheet URL: {sheets.spreadsheet.url}")

    return sheets.spreadsheet.url
