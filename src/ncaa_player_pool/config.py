"""
Configuration management for NCAA Player Pool application.
Loads settings from environment variables and provides defaults.
"""

import os
from dataclasses import dataclass
from pathlib import Path

import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()


@dataclass
class Config:
    """Application configuration."""

    # Database
    postgres_conn_str: str
    database_schema: str = "ncaa_pool"

    # ESPN API
    espn_base_url: str = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
    espn_api_key: str | None = None  # ESPN public API doesn't require key for basic endpoints

    # Application
    tournament_year: int = 2026
    data_dir: Path = Path("data")
    log_level: str = "INFO"
    log_file: str | None = "logs/ncaa_pool.log"

    # HTTP Client
    request_timeout: int = 30  # seconds
    max_retries: int = 3
    retry_backoff_factor: float = 1.0  # exponential backoff: {backoff factor} * (2 ** retry_count)
    rate_limit_delay: float = 2.5  # seconds between requests

    # Google Sheets
    google_credentials_file: str | None = None
    google_sheet_id: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        """
        Create configuration from environment variables.

        Returns:
            Config instance populated from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        postgres_conn_str = os.getenv("POSTGRES_CONN_STR")
        if not postgres_conn_str:
            raise ValueError("POSTGRES_CONN_STR environment variable is required")

        return cls(
            postgres_conn_str=postgres_conn_str,
            database_schema=os.getenv("DATABASE_SCHEMA", "ncaa_pool"),
            espn_api_key=os.getenv("ESPN_API_KEY"),
            tournament_year=int(os.getenv("TOURNAMENT_YEAR", "2026")),
            data_dir=Path(os.getenv("DATA_DIR", "data")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/ncaa_pool.log"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_backoff_factor=float(os.getenv("RETRY_BACKOFF_FACTOR", "1.0")),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "2.5")),
            google_credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE"),
            google_sheet_id=os.getenv("GOOGLE_SHEET_ID"),
        )

    def get_espn_tournament_url(self, tournament_id: str | None = None) -> str:
        """
        Get ESPN tournament summary URL.

        Args:
            tournament_id: Optional specific tournament ID. If None, uses general tournament endpoint

        Returns:
            Full tournament URL
        """
        if tournament_id:
            return f"{self.espn_base_url}/tournaments/{tournament_id}/summary.json"
        return f"{self.espn_base_url}/scoreboard"

    def get_espn_team_url(self, team_id: str) -> str:
        """
        Get ESPN team profile URL.

        Args:
            team_id: Team identifier

        Returns:
            Full team profile URL
        """
        return f"{self.espn_base_url}/teams/{team_id}"

    def get_espn_game_url(self, game_id: str) -> str:
        """
        Get ESPN game summary URL.

        Args:
            game_id: Game identifier

        Returns:
            Full game summary URL
        """
        return f"{self.espn_base_url}/summary?event={game_id}"


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance

    Raises:
        ValueError: If configuration hasn't been initialized
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """Reset the global configuration (mainly for testing)."""
    global _config
    _config = None
