"""
Google Sheets integration for NCAA Player Pool.
Exports player roster and game statistics to Google Sheets.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from logger import get_logger
from config import Config

logger = get_logger(__name__)


class SheetsClient:
    """Google Sheets client for exporting NCAA pool data."""

    # Google Sheets API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, config: Config):
        """
        Initialize Google Sheets client.

        Args:
            config: Application configuration
        """
        self.config = config
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None

    def authenticate(self):
        """
        Authenticate with Google Sheets API using service account.

        Raises:
            FileNotFoundError: If credentials file not found
            Exception: If authentication fails
        """
        if not self.config.google_credentials_file:
            raise ValueError("GOOGLE_CREDENTIALS_FILE not set in environment")

        creds_path = Path(self.config.google_credentials_file)
        if not creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found: {creds_path}")

        try:
            credentials = Credentials.from_service_account_file(
                str(creds_path),
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(credentials)
            logger.info("Successfully authenticated with Google Sheets API")

        except Exception as e:
            logger.exception(f"Failed to authenticate with Google Sheets: {e}")
            raise

    def open_spreadsheet(self, sheet_id: Optional[str] = None):
        """
        Open a Google Spreadsheet.

        Args:
            sheet_id: Spreadsheet ID (uses config if not provided)

        Raises:
            ValueError: If sheet_id not provided and not in config
            Exception: If spreadsheet cannot be opened
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
        """
        Get existing worksheet or create new one.

        Args:
            title: Worksheet title
            rows: Number of rows (default 1000)
            cols: Number of columns (default 26)

        Returns:
            Worksheet object
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

    def export_players(self, players_data: List[Dict[str, Any]], worksheet_name: str = "Players"):
        """
        Export tournament player roster to Google Sheets.

        Columns: Player ID, Player Name, Position, Team, Team Seed

        Args:
            players_data: List of player dictionaries from database
            worksheet_name: Name of worksheet to write to
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
        worksheet.update(rows, value_input_option='RAW')

        # Format header row
        worksheet.format('A1:F1', {
            "backgroundColor": {"red": 0.2, "green": 0.5, "blue": 0.8},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER"
        })

        # Freeze header row
        worksheet.freeze(rows=1)

        logger.info(f"Successfully exported {len(players_data)} players")

    def export_player_stats(self, stats_data: List[Dict[str, Any]], worksheet_name: str = "Player Stats"):
        """
        Export detailed player game statistics to Google Sheets.

        Columns: Player ID, Is Eliminated, Player Name, Position, Team, Game ID,
                Round, Points, Assists, Rebounds, Steals, Minutes Played, etc.

        Args:
            stats_data: List of game stats dictionaries from database
            worksheet_name: Name of worksheet to write to
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
            "Total Score (PTS+AST+REB)"
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
        worksheet.update(rows, value_input_option='RAW')

        # Format header row
        worksheet.format('A1:T1', {
            "backgroundColor": {"red": 0.2, "green": 0.5, "blue": 0.8},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER",
            "wrapStrategy": "WRAP"
        })

        # Format eliminated column with conditional colors
        # Green for No (active), Red for Yes (eliminated)
        worksheet.format('B2:B5000', {
            "horizontalAlignment": "CENTER"
        })

        # Format stat columns as numbers
        stat_cols = ['L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']  # Points through Total Score
        for col in stat_cols:
            worksheet.format(f'{col}2:{col}5000', {
                "horizontalAlignment": "RIGHT",
                "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
            })

        # Bold and highlight total score column
        worksheet.format('T2:T5000', {
            "textFormat": {"bold": True}
        })

        # Freeze header row
        worksheet.freeze(rows=1)

        logger.info(f"Successfully exported {len(stats_data)} stat records")


def export_all_data(config: Config, year: int, sheet_id: Optional[str] = None) -> str:
    """
    Export all data (players and stats) to Google Sheets.

    Args:
        config: Application configuration
        year: Tournament year
        sheet_id: Optional Google Sheet ID (uses config if not provided)

    Returns:
        Spreadsheet URL
    """
    from db import Database

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
