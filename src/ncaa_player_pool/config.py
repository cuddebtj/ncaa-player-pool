"""Configuration management for NCAA Player Pool application.

This module provides centralized configuration management, loading settings
from environment variables with sensible defaults. Configuration includes
database connections, ESPN API settings, HTTP client parameters, and
Google Sheets integration.

The module uses a singleton pattern via `get_config()` to ensure consistent
configuration access throughout the application.

Example:
    Basic usage::

        from ncaa_player_pool.config import get_config

        config = get_config()
        print(f"Tournament year: {config.tournament_year}")
        print(f"Database schema: {config.database_schema}")

    Creating custom configuration::

        from ncaa_player_pool.config import Config

        config = Config(
            postgres_conn_str="postgresql://localhost/ncaa",
            tournament_year=2026,
        )

Environment Variables:
    POSTGRES_CONN_STR: PostgreSQL connection string (required).
    DATABASE_SCHEMA: Database schema name (default: "ncaa_pool").
    ESPN_API_KEY: ESPN API key if required (default: None).
    TOURNAMENT_YEAR: Target tournament year (default: 2026).
    DATA_DIR: Directory for cached data (default: "data").
    LOG_LEVEL: Logging level (default: "INFO").
    LOG_FILE: Log file path (default: "logs/ncaa_pool.log").
    REQUEST_TIMEOUT: HTTP timeout in seconds (default: 30).
    MAX_RETRIES: Maximum retry attempts (default: 3).
    RETRY_BACKOFF_FACTOR: Exponential backoff multiplier (default: 1.0).
    RATE_LIMIT_DELAY: Delay between requests in seconds (default: 2.5).
    GOOGLE_CREDENTIALS_FILE: Path to Google service account JSON.
    GOOGLE_SHEET_ID: Target Google Sheets spreadsheet ID.
"""

import os
from dataclasses import dataclass
from pathlib import Path

import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()


@dataclass
class Config:
    """Application configuration container.

    Stores all configuration parameters for the NCAA Player Pool application.
    Can be instantiated directly or created from environment variables using
    the `from_env()` class method.

    Attributes:
        postgres_conn_str: PostgreSQL connection string including credentials.
        database_schema: Database schema name for all tables.
        espn_base_url: Base URL for ESPN API endpoints.
        espn_api_key: Optional ESPN API key (not required for public endpoints).
        tournament_year: Target NCAA tournament year.
        data_dir: Directory path for caching API responses.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Path to log file, or None for console-only logging.
        request_timeout: HTTP request timeout in seconds.
        max_retries: Maximum number of retry attempts for failed requests.
        retry_backoff_factor: Multiplier for exponential backoff calculation.
        rate_limit_delay: Minimum seconds between consecutive API requests.
        google_credentials_file: Path to Google service account JSON file.
        google_sheet_id: Google Sheets spreadsheet ID for exports.

    Example:
        >>> config = Config(
        ...     postgres_conn_str="postgresql://user:pass@localhost/ncaa",
        ...     tournament_year=2026,
        ... )
        >>> config.get_espn_team_url("150")
        'https://site.api.espn.com/.../teams/150'
    """

    # Database
    postgres_conn_str: str
    database_schema: str = "ncaa_pool"

    # ESPN API
    espn_base_url: str = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
    espn_api_key: str | None = None

    # Application
    tournament_year: int = 2026
    data_dir: Path = Path("data")
    log_level: str = "INFO"
    log_file: str | None = "logs/ncaa_pool.log"

    # HTTP Client
    request_timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 1.0
    rate_limit_delay: float = 2.5

    # Google Sheets
    google_credentials_file: str | None = None
    google_sheet_id: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables.

        Reads all configuration values from environment variables,
        using defaults where appropriate. The POSTGRES_CONN_STR
        variable is required.

        Returns:
            Config: Fully populated configuration instance.

        Raises:
            ValueError: If POSTGRES_CONN_STR is not set.

        Example:
            >>> import os
            >>> os.environ["POSTGRES_CONN_STR"] = "postgresql://localhost/ncaa"
            >>> config = Config.from_env()
            >>> config.database_schema
            'ncaa_pool'
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
        """Build ESPN tournament API URL.

        Constructs the full URL for fetching tournament bracket data
        from the ESPN API.

        Args:
            tournament_id: Specific tournament identifier. If None,
                returns the general scoreboard URL.

        Returns:
            Complete ESPN API URL for tournament data.

        Example:
            >>> config.get_espn_tournament_url("22")
            'https://site.api.espn.com/.../tournaments/22/summary.json'
        """
        if tournament_id:
            return f"{self.espn_base_url}/tournaments/{tournament_id}/summary.json"
        return f"{self.espn_base_url}/scoreboard"

    def get_espn_team_url(self, team_id: str) -> str:
        """Build ESPN team profile API URL.

        Args:
            team_id: ESPN team identifier.

        Returns:
            Complete ESPN API URL for team data.

        Example:
            >>> config.get_espn_team_url("150")
            'https://site.api.espn.com/.../teams/150'
        """
        return f"{self.espn_base_url}/teams/{team_id}"

    def get_espn_game_url(self, game_id: str) -> str:
        """Build ESPN game summary API URL.

        Args:
            game_id: ESPN game/event identifier.

        Returns:
            Complete ESPN API URL for game summary with box score.

        Example:
            >>> config.get_espn_game_url("401234567")
            'https://site.api.espn.com/.../summary?event=401234567'
        """
        return f"{self.espn_base_url}/summary?event={game_id}"


# Global config instance (singleton pattern)
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns the singleton Config instance, creating it from environment
    variables on first call. Subsequent calls return the same instance.

    Returns:
        The global Config instance.

    Raises:
        ValueError: If required environment variables are missing on
            first initialization.

    Example:
        >>> config = get_config()
        >>> config.tournament_year
        2026
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance.

    Clears the singleton Config instance, causing the next call to
    `get_config()` to reload from environment variables. Primarily
    useful for testing.

    Example:
        >>> reset_config()
        >>> # Next get_config() will reload from environment
    """
    global _config
    _config = None
