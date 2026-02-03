"""Tests for Pydantic data models."""

import importlib
import sys
from pathlib import Path

# Add the package directory to the path for testing
package_dir = Path(__file__).parent.parent
sys.path.insert(0, str(package_dir))

# Import from the hyphenated package name
models = importlib.import_module("ncaa-player-pool.models")
ESPNAthlete = models.ESPNAthlete
ESPNPlayerStats = models.ESPNPlayerStats
ESPNPosition = models.ESPNPosition
ESPNTeamBasic = models.ESPNTeamBasic


class TestESPNTeamBasic:
    """Tests for ESPNTeamBasic model."""

    def test_create_team_basic(self, sample_team: dict) -> None:
        """Test creating a basic team model."""
        team = ESPNTeamBasic(**sample_team)
        assert team.id == "99"
        assert team.displayName == "Test University"
        assert team.abbreviation == "TEST"
        assert team.location == "Test City"

    def test_team_optional_fields(self) -> None:
        """Test team with only required fields."""
        team = ESPNTeamBasic(
            id="1",
            displayName="Minimal Team",
            abbreviation="MIN",
        )
        assert team.id == "1"
        assert team.location is None
        assert team.logo is None


class TestESPNPosition:
    """Tests for ESPNPosition model."""

    def test_create_position(self) -> None:
        """Test creating a position model."""
        position = ESPNPosition(
            name="Guard",
            displayName="Point Guard",
            abbreviation="PG",
        )
        assert position.name == "Guard"
        assert position.abbreviation == "PG"


class TestESPNAthlete:
    """Tests for ESPNAthlete model."""

    def test_create_athlete(self, sample_player_stats: dict) -> None:
        """Test creating an athlete model."""
        athlete_data = sample_player_stats["athlete"]
        athlete = ESPNAthlete(**athlete_data)
        assert athlete.id == "12345"
        assert athlete.displayName == "Test Player"
        assert athlete.jersey == "23"
        assert athlete.position is not None
        assert athlete.position.abbreviation == "PG"


class TestESPNPlayerStats:
    """Tests for ESPNPlayerStats model."""

    def test_create_player_stats(self, sample_player_stats: dict) -> None:
        """Test creating a player stats model."""
        stats = ESPNPlayerStats(**sample_player_stats)
        assert stats.athlete.id == "12345"
        assert stats.starter is True
        assert stats.didNotPlay is False
        assert len(stats.stats) == 12

    def test_get_stat(self, sample_player_stats: dict, sample_stat_keys: list[str]) -> None:
        """Test getting a specific stat value."""
        stats = ESPNPlayerStats(**sample_player_stats)
        assert stats.get_stat(sample_stat_keys, "PTS") == "22"
        assert stats.get_stat(sample_stat_keys, "REB") == "7"
        assert stats.get_stat(sample_stat_keys, "AST") == "3"

    def test_get_stat_invalid_key(self, sample_player_stats: dict, sample_stat_keys: list[str]) -> None:
        """Test getting an invalid stat returns None."""
        stats = ESPNPlayerStats(**sample_player_stats)
        assert stats.get_stat(sample_stat_keys, "INVALID") is None

    def test_parse_points(self, sample_player_stats: dict, sample_stat_keys: list[str]) -> None:
        """Test parsing points from stats."""
        stats = ESPNPlayerStats(**sample_player_stats)
        assert stats.parse_points(sample_stat_keys) == 22

    def test_parse_rebounds(self, sample_player_stats: dict, sample_stat_keys: list[str]) -> None:
        """Test parsing rebounds from stats."""
        stats = ESPNPlayerStats(**sample_player_stats)
        assert stats.parse_rebounds(sample_stat_keys) == 7

    def test_parse_assists(self, sample_player_stats: dict, sample_stat_keys: list[str]) -> None:
        """Test parsing assists from stats."""
        stats = ESPNPlayerStats(**sample_player_stats)
        assert stats.parse_assists(sample_stat_keys) == 3

    def test_parse_stats_with_non_numeric(self) -> None:
        """Test parsing stats when value is not numeric."""
        stats = ESPNPlayerStats(
            athlete=ESPNAthlete(id="1", displayName="Test"),
            starter=False,
            didNotPlay=True,
            stats=["--", "--", "--"],
        )
        keys = ["PTS", "REB", "AST"]
        assert stats.parse_points(keys) == 0
        assert stats.parse_rebounds(keys) == 0
        assert stats.parse_assists(keys) == 0
