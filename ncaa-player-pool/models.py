"""
Pydantic data models for NCAA Player Pool application.
Models ESPN API responses and database entities.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

# ============================================
# ESPN API Response Models
# ============================================


class ESPNTeamBasic(BaseModel):
    """Basic team information from ESPN API."""

    id: str
    displayName: str
    abbreviation: str
    location: str | None = None
    name: str | None = None
    logo: str | None = None
    color: str | None = None


class ESPNPosition(BaseModel):
    """Player position information."""

    name: str
    displayName: str | None = None
    abbreviation: str


class ESPNAthlete(BaseModel):
    """Athlete/player information from ESPN API."""

    id: str
    displayName: str
    shortName: str | None = None
    jersey: str | None = None
    position: ESPNPosition | None = None


class ESPNPlayerStats(BaseModel):
    """Player statistics from game box score."""

    athlete: ESPNAthlete
    starter: bool = False
    didNotPlay: bool = False
    stats: list[str]  # Array of stat values as strings

    def get_stat(self, keys: list[str], stat_name: str) -> str | None:
        """Get a specific stat value by name."""
        try:
            index = keys.index(stat_name)
            return self.stats[index] if index < len(self.stats) else None
        except (ValueError, IndexError):
            return None

    def parse_points(self, keys: list[str]) -> int:
        """Parse points from stats array."""
        pts = self.get_stat(keys, "PTS")
        return int(pts) if pts and pts.isdigit() else 0

    def parse_rebounds(self, keys: list[str]) -> int:
        """Parse total rebounds from stats array."""
        reb = self.get_stat(keys, "REB")
        return int(reb) if reb and reb.isdigit() else 0

    def parse_assists(self, keys: list[str]) -> int:
        """Parse assists from stats array."""
        ast = self.get_stat(keys, "AST")
        return int(ast) if ast and ast.isdigit() else 0


class ESPNPlayerStatsGroup(BaseModel):
    """Group of player statistics with keys."""

    names: list[str] | None = None  # Alternative to name
    name: str | None = None
    keys: list[str]  # Stat keys like ["MIN", "FG", "3PT", ...]
    labels: list[str]
    descriptions: list[str] | None = None
    athletes: list[ESPNPlayerStats]
    totals: list[str] | None = None


class ESPNBoxscoreTeam(BaseModel):
    """Team box score information."""

    team: ESPNTeamBasic
    statistics: list[dict] | None = None


class ESPNBoxscorePlayers(BaseModel):
    """Player statistics for a team."""

    team: ESPNTeamBasic
    statistics: list[ESPNPlayerStatsGroup]


class ESPNBoxscore(BaseModel):
    """Game box score with team and player statistics."""

    teams: list[ESPNBoxscoreTeam]
    players: list[ESPNBoxscorePlayers]


class ESPNCompetitor(BaseModel):
    """Competitor (team) in a game."""

    id: str
    homeAway: str
    team: ESPNTeamBasic
    score: str | None = None
    winner: bool | None = None


class ESPNCompetition(BaseModel):
    """Competition information from game/event."""

    id: str
    date: str
    attendance: int | None = None
    competitors: list[ESPNCompetitor]


class ESPNGameHeader(BaseModel):
    """Game header information."""

    id: str
    competitions: list[ESPNCompetition]


class ESPNGameSummary(BaseModel):
    """Complete game summary response."""

    header: ESPNGameHeader
    boxscore: ESPNBoxscore


class ESPNEvent(BaseModel):
    """Event (game) from scoreboard."""

    id: str
    date: str
    name: str
    shortName: str | None = None
    competitions: list[ESPNCompetition]


class ESPNScoreboard(BaseModel):
    """Scoreboard response with events."""

    events: list[ESPNEvent]


class ESPNTeamRecord(BaseModel):
    """Team record information."""

    summary: str | None = None


class ESPNTeamDetail(BaseModel):
    """Detailed team information."""

    id: str
    displayName: str
    abbreviation: str
    location: str
    name: str
    slug: str
    color: str | None = None
    logos: list[dict] | None = None
    record: dict | None = None
    rank: int | None = None


class ESPNTeamResponse(BaseModel):
    """Team API response."""

    team: ESPNTeamDetail


class ESPNRosterAthlete(BaseModel):
    """Athlete from roster endpoint."""

    id: str
    firstName: str | None = None
    lastName: str | None = None
    fullName: str
    displayName: str
    shortName: str | None = None
    jersey: str | None = None
    position: ESPNPosition | None = None
    height: float | None = None
    displayHeight: str | None = None
    weight: float | None = None
    displayWeight: str | None = None
    experience: dict | None = None
    status: dict | None = None


class ESPNRosterResponse(BaseModel):
    """Roster API response."""

    team: ESPNTeamBasic
    athletes: list[ESPNRosterAthlete]
    season: dict | None = None


class ESPNTournamentParticipant(BaseModel):
    """Tournament bracket participant (team with seed)."""

    id: str
    name: str
    market: str | None = None
    seed: int | None = None
    type: str = "team"


class ESPNTournamentGame(BaseModel):
    """Tournament bracket game."""

    id: str
    scheduled: str | None = None


class ESPNTournamentBracket(BaseModel):
    """Tournament bracket/region."""

    id: str
    name: str
    location: str | None = None
    participants: list[ESPNTournamentParticipant] = []
    games: list[ESPNTournamentGame] = []


class ESPNTournament(BaseModel):
    """Tournament response."""

    id: str
    name: str
    status: str
    start_date: str | None = None
    end_date: str | None = None
    brackets: list[ESPNTournamentBracket] = []


# ============================================
# Database Models
# ============================================


class Tournament(BaseModel):
    """Tournament database model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    year: int
    status: str = "upcoming"  # upcoming, in_progress, completed
    start_date: datetime | None = None
    end_date: datetime | None = None
    raw_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Team(BaseModel):
    """Team database model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    market: str | None = None  # School name (e.g., "Duke", "UConn")
    abbreviation: str | None = None
    seed: int | None = None  # 1-16, null for regular season
    year: int
    eliminated: bool = False
    eliminated_round: str | None = None
    raw_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Player(BaseModel):
    """Player database model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    team_id: str
    full_name: str
    short_name: str | None = None
    position: str | None = None
    jersey_number: str | None = None
    year: int
    active: bool = True
    raw_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Game(BaseModel):
    """Game database model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    home_team_id: str
    away_team_id: str
    year: int
    round_name: str | None = None
    scheduled_date: datetime | None = None
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    home_score: int | None = None
    away_score: int | None = None
    winner_team_id: str | None = None
    raw_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PlayerGameStats(BaseModel):
    """Player game statistics database model."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    game_id: str
    player_id: str
    team_id: str
    year: int
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    minutes_played: int | None = None
    field_goals_made: int | None = None
    field_goals_attempted: int | None = None
    three_pointers_made: int | None = None
    three_pointers_attempted: int | None = None
    free_throws_made: int | None = None
    free_throws_attempted: int | None = None
    steals: int | None = None
    blocks: int | None = None
    turnovers: int | None = None
    fouls: int | None = None
    starter: bool = False
    did_not_play: bool = False
    raw_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def total_score(self) -> int:
        """Calculate total score (points + rebounds + assists)."""
        return self.points + self.rebounds + self.assists


# ============================================
# View Models for Google Sheets Export
# ============================================


class PlayerExport(BaseModel):
    """Player data for Google Sheets export."""

    player_id: str
    player_name: str
    position: str | None = None
    jersey_number: str | None = None
    team_id: str
    team_name: str
    seed: int | None = None
    eliminated: bool = False
    tournament_year: int
    active: bool = True


class PlayerStatsExport(BaseModel):
    """Player tournament statistics for export."""

    player_id: str
    player_name: str
    team_name: str
    seed: int | None = None
    tournament_year: int
    games_played: int = 0
    total_points: int = 0
    total_rebounds: int = 0
    total_assists: int = 0
    total_score: int = 0
    avg_points: float = 0.0
    avg_rebounds: float = 0.0
    avg_assists: float = 0.0
    eliminated: bool = False


class GameStatsExport(BaseModel):
    """Game-by-game statistics for export."""

    game_id: str
    tournament_year: int
    round_name: str | None = None
    scheduled_date: datetime | None = None
    game_status: str
    home_team: str
    away_team: str
    home_score: int | None = None
    away_score: int | None = None
    player_name: str
    player_team: str
    seed: int | None = None
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    total_score: int = 0
    minutes_played: int | None = None
