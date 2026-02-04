"""NCAA Tournament Player Pool - Track player stats and manage pool entries.

This package provides tools for managing NCAA Tournament player pools,
including automatic data collection from ESPN, PostgreSQL storage,
and Google Sheets integration for sharing results.

Example:
    Basic usage with the CLI::

        ./ncaa-pool fetch-tournament --year 2026
        ./ncaa-pool fetch-rosters --year 2026
        ./ncaa-pool update-stats --year 2026
        ./ncaa-pool export --year 2026

    Programmatic usage::

        from ncaa_player_pool.config import get_config
        from ncaa_player_pool.db import Database
        from ncaa_player_pool.espn_api import ESPNService

        config = get_config()
        db = Database(config)
        espn = ESPNService(config)

Modules:
    models: Pydantic data models for ESPN API and database entities.
    config: Configuration management via environment variables.
    logger: Logging utilities with file rotation.
    api_client: HTTP client with retry logic.
    db: PostgreSQL database operations.
    espn_api: ESPN API integration.
    transformers: Data transformation functions.
    sheets: Google Sheets export functionality.
"""

__version__ = "0.1.0"
__author__ = "NCAA Player Pool Team"

# Public API exports
from .config import Config, get_config, reset_config
from .logger import get_logger, setup_logger
from .models import (
    # Database models
    Game,
    # Export models
    GameStatsExport,
    Player,
    PlayerExport,
    PlayerGameStats,
    PlayerStatsExport,
    Team,
    Tournament,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Config
    "Config",
    "get_config",
    "reset_config",
    # Logging
    "get_logger",
    "setup_logger",
    # Database models
    "Tournament",
    "Team",
    "Player",
    "Game",
    "PlayerGameStats",
    # Export models
    "PlayerExport",
    "PlayerStatsExport",
    "GameStatsExport",
]
