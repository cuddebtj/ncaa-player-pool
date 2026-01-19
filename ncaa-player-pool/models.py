"""
Pydantic data models for NCAA Player Pool application.
Models ESPN API responses and database entities.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# ESPN API Response Models
# ============================================

class ESPNTeamBasic(BaseModel):
    """Basic team information from ESPN API."""
    id: str
    displayName: str
    abbreviation: str
    location: Optional[str] = None
    name: Optional[str] = None
    logo: Optional[str] = None
    color: Optional[str] = None


class ESPNPosition(BaseModel):
    """Player position information."""
    name: str
    displayName: Optional[str] = None
    abbreviation: str


class ESPNAthlete(BaseModel):
    """Athlete/player information from ESPN API."""
    id: str
    displayName: str
    shortName: Optional[str] = None
    jersey: Optional[str] = None
    position: Optional[ESPNPosition] = None


class ESPNPlayerStats(BaseModel):
    """Player statistics from game box score."""
    athlete: ESPNAthlete
    starter: bool = False
    didNotPlay: bool = False
    stats: List[str]  # Array of stat values as strings

    def get_stat(self, keys: List[str], stat_name: str) -> Optional[str]:
        """Get a specific stat value by name."""
        try:
            index = keys.index(stat_name)
            return self.stats[index] if index < len(self.stats) else None
        except (ValueError, IndexError):
            return None

    def parse_points(self, keys: List[str]) -> int:
        """Parse points from stats array."""
        pts = self.get_stat(keys, "PTS")
        return int(pts) if pts and pts.isdigit() else 0

    def parse_rebounds(self, keys: List[str]) -> int:
        """Parse total rebounds from stats array."""
        reb = self.get_stat(keys, "REB")
        return int(reb) if reb and reb.isdigit() else 0

    def parse_assists(self, keys: List[str]) -> int:
        """Parse assists from stats array."""
        ast = self.get_stat(keys, "AST")
        return int(ast) if ast and ast.isdigit() else 0


class ESPNPlayerStatsGroup(BaseModel):
    """Group of player statistics with keys."""
    names: Optional[List[str]] = None  # Alternative to name
    name: Optional[str] = None
    keys: List[str]  # Stat keys like ["MIN", "FG", "3PT", ...]
    labels: List[str]
    descriptions: Optional[List[str]] = None
    athletes: List[ESPNPlayerStats]
    totals: Optional[List[str]] = None


class ESPNBoxscoreTeam(BaseModel):
    """Team box score information."""
    team: ESPNTeamBasic
    statistics: Optional[List[dict]] = None


class ESPNBoxscorePlayers(BaseModel):
    """Player statistics for a team."""
    team: ESPNTeamBasic
    statistics: List[ESPNPlayerStatsGroup]


class ESPNBoxscore(BaseModel):
    """Game box score with team and player statistics."""
    teams: List[ESPNBoxscoreTeam]
    players: List[ESPNBoxscorePlayers]


class ESPNCompetitor(BaseModel):
    """Competitor (team) in a game."""
    id: str
    homeAway: str
    team: ESPNTeamBasic
    score: Optional[str] = None
    winner: Optional[bool] = None


class ESPNCompetition(BaseModel):
    """Competition information from game/event."""
    id: str
    date: str
    attendance: Optional[int] = None
    competitors: List[ESPNCompetitor]


class ESPNGameHeader(BaseModel):
    """Game header information."""
    id: str
    competitions: List[ESPNCompetition]


class ESPNGameSummary(BaseModel):
    """Complete game summary response."""
    header: ESPNGameHeader
    boxscore: ESPNBoxscore


class ESPNEvent(BaseModel):
    """Event (game) from scoreboard."""
    id: str
    date: str
    name: str
    shortName: Optional[str] = None
    competitions: List[ESPNCompetition]


class ESPNScoreboard(BaseModel):
    """Scoreboard response with events."""
    events: List[ESPNEvent]


class ESPNTeamRecord(BaseModel):
    """Team record information."""
    summary: Optional[str] = None


class ESPNTeamDetail(BaseModel):
    """Detailed team information."""
    id: str
    displayName: str
    abbreviation: str
    location: str
    name: str
    slug: str
    color: Optional[str] = None
    logos: Optional[List[dict]] = None
    record: Optional[dict] = None
    rank: Optional[int] = None


class ESPNTeamResponse(BaseModel):
    """Team API response."""
    team: ESPNTeamDetail


class ESPNRosterAthlete(BaseModel):
    """Athlete from roster endpoint."""
    id: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    fullName: str
    displayName: str
    shortName: Optional[str] = None
    jersey: Optional[str] = None
    position: Optional[ESPNPosition] = None
    height: Optional[float] = None
    displayHeight: Optional[str] = None
    weight: Optional[float] = None
    displayWeight: Optional[str] = None
    experience: Optional[dict] = None
    status: Optional[dict] = None


class ESPNRosterResponse(BaseModel):
    """Roster API response."""
    team: ESPNTeamBasic
    athletes: List[ESPNRosterAthlete]
    season: Optional[dict] = None


class ESPNTournamentParticipant(BaseModel):
    """Tournament bracket participant (team with seed)."""
    id: str
    name: str
    market: Optional[str] = None
    seed: Optional[int] = None
    type: str = "team"


class ESPNTournamentGame(BaseModel):
    """Tournament bracket game."""
    id: str
    scheduled: Optional[str] = None


class ESPNTournamentBracket(BaseModel):
    """Tournament bracket/region."""
    id: str
    name: str
    location: Optional[str] = None
    participants: List[ESPNTournamentParticipant] = []
    games: List[ESPNTournamentGame] = []


class ESPNTournament(BaseModel):
    """Tournament response."""
    id: str
    name: str
    status: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    brackets: List[ESPNTournamentBracket] = []


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
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    raw_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Team(BaseModel):
    """Team database model."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    market: Optional[str] = None  # School name (e.g., "Duke", "UConn")
    abbreviation: Optional[str] = None
    seed: Optional[int] = None  # 1-16, null for regular season
    year: int
    eliminated: bool = False
    eliminated_round: Optional[str] = None
    raw_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Player(BaseModel):
    """Player database model."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    team_id: str
    full_name: str
    short_name: Optional[str] = None
    position: Optional[str] = None
    jersey_number: Optional[str] = None
    year: int
    active: bool = True
    raw_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Game(BaseModel):
    """Game database model."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    home_team_id: str
    away_team_id: str
    year: int
    round_name: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    winner_team_id: Optional[str] = None
    raw_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PlayerGameStats(BaseModel):
    """Player game statistics database model."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    game_id: str
    player_id: str
    team_id: str
    year: int
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    minutes_played: Optional[int] = None
    field_goals_made: Optional[int] = None
    field_goals_attempted: Optional[int] = None
    three_pointers_made: Optional[int] = None
    three_pointers_attempted: Optional[int] = None
    free_throws_made: Optional[int] = None
    free_throws_attempted: Optional[int] = None
    steals: Optional[int] = None
    blocks: Optional[int] = None
    turnovers: Optional[int] = None
    fouls: Optional[int] = None
    starter: bool = False
    did_not_play: bool = False
    raw_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    position: Optional[str] = None
    jersey_number: Optional[str] = None
    team_id: str
    team_name: str
    seed: Optional[int] = None
    eliminated: bool = False
    tournament_year: int
    active: bool = True


class PlayerStatsExport(BaseModel):
    """Player tournament statistics for export."""
    player_id: str
    player_name: str
    team_name: str
    seed: Optional[int] = None
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
    round_name: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    game_status: str
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    player_name: str
    player_team: str
    seed: Optional[int] = None
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    total_score: int = 0
    minutes_played: Optional[int] = None
