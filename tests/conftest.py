"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add the project root to the path for importing the hyphenated package
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def data_dir() -> Path:
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_player_stats() -> dict:
    """Sample player stats data for testing."""
    return {
        "athlete": {
            "id": "12345",
            "displayName": "Test Player",
            "shortName": "T. Player",
            "jersey": "23",
            "position": {
                "name": "Guard",
                "displayName": "Point Guard",
                "abbreviation": "PG",
            },
        },
        "starter": True,
        "didNotPlay": False,
        "stats": ["32", "8-15", "2-5", "4-4", "2", "5", "7", "3", "1", "2", "3", "22"],
    }


@pytest.fixture
def sample_stat_keys() -> list[str]:
    """Sample stat keys matching the stats array order."""
    return ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PTS"]


@pytest.fixture
def sample_team() -> dict:
    """Sample team data for testing."""
    return {
        "id": "99",
        "displayName": "Test University",
        "abbreviation": "TEST",
        "location": "Test City",
        "name": "Testers",
        "logo": "https://example.com/logo.png",
        "color": "FF0000",
    }
