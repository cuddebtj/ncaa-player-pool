"""Pydantic data models for NCAA Player Pool application.

This module defines all data models used throughout the application, including:

- ESPN API response models for parsing JSON data from ESPN endpoints
- Database models representing PostgreSQL entities
- Export models for Google Sheets data formatting

The models use Pydantic for validation and serialization, supporting both
API response parsing and database ORM compatibility.

Example:
    Parsing an ESPN roster response::

        from ncaa_player_pool.models import ESPNRosterResponse

        response_data = await api_client.get("/roster")
        roster = ESPNRosterResponse.model_validate(response_data)
        for athlete in roster.athletes:
            print(f"{athlete.fullName} - #{athlete.jersey}")

    Creating a database model::

        from ncaa_player_pool.models import Player

        player = Player(
            id="12345",
            team_id="99",
            full_name="John Smith",
            position="G",
            year=2026,
        )
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

# ============================================
# ESPN API Response Models
# ============================================


class ESPNTeamBasic(BaseModel):
    """Basic team information from ESPN API responses.

    This model represents the minimal team data returned in most ESPN
    API endpoints. It captures identifying information and optional
    display properties.

    Attributes:
        id: ESPN's unique identifier for the team.
        displayName: Full team name (e.g., "Duke Blue Devils").
        abbreviation: Short team code (e.g., "DUKE").
        location: City or school name (e.g., "Duke").
        name: Team mascot/nickname (e.g., "Blue Devils").
        logo: URL to team logo image.
        color: Primary team color as hex code.

    Example:
        >>> team = ESPNTeamBasic(
        ...     id="150",
        ...     displayName="Duke Blue Devils",
        ...     abbreviation="DUKE"
        ... )
        >>> team.displayName
        'Duke Blue Devils'
    """

    id: str
    displayName: str
    abbreviation: str
    location: str | None = None
    name: str | None = None
    logo: str | None = None
    color: str | None = None


class ESPNPosition(BaseModel):
    """Player position information from ESPN API.

    Represents a basketball position with various name formats
    for different display contexts.

    Attributes:
        name: Full position name (e.g., "Guard").
        displayName: Display-friendly name (e.g., "Point Guard").
        abbreviation: Short position code (e.g., "PG", "SF", "C").

    Example:
        >>> pos = ESPNPosition(name="Guard", abbreviation="PG")
        >>> pos.abbreviation
        'PG'
    """

    name: str
    displayName: str | None = None
    abbreviation: str


class ESPNAthlete(BaseModel):
    """Athlete/player information from ESPN API.

    Contains basic player identification used across various
    ESPN endpoints including box scores and rosters.

    Attributes:
        id: ESPN's unique player identifier.
        displayName: Full player name (e.g., "LeBron James").
        shortName: Abbreviated name (e.g., "L. James").
        jersey: Jersey number as string (e.g., "23").
        position: Player's position information.

    Example:
        >>> athlete = ESPNAthlete(
        ...     id="12345",
        ...     displayName="John Smith",
        ...     jersey="23"
        ... )
    """

    id: str
    displayName: str
    shortName: str | None = None
    jersey: str | None = None
    position: ESPNPosition | None = None


class ESPNPlayerStats(BaseModel):
    """Player statistics from a game box score.

    Contains an athlete's performance data for a single game,
    with stats stored as an ordered array of string values.

    Attributes:
        athlete: The player's identification information.
        starter: Whether the player started the game.
        didNotPlay: Whether the player was inactive/DNP.
        stats: Ordered array of stat values as strings. The order
            corresponds to stat keys provided by ESPNPlayerStatsGroup.

    Example:
        >>> stats = ESPNPlayerStats(
        ...     athlete=ESPNAthlete(id="1", displayName="Test"),
        ...     starter=True,
        ...     stats=["32", "8-15", "2-5", "4-4", "7", "3", "22"]
        ... )
        >>> stats.parse_points(["MIN", "FG", "3PT", "FT", "REB", "AST", "PTS"])
        22
    """

    athlete: ESPNAthlete
    starter: bool = False
    didNotPlay: bool = False
    stats: list[str]  # Array of stat values as strings

    def get_stat(self, keys: list[str], stat_name: str) -> str | None:
        """Retrieve a specific statistic value by name.

        Looks up the stat name in the keys list to find its index,
        then returns the corresponding value from the stats array.

        Args:
            keys: List of stat key names in the same order as self.stats.
            stat_name: The stat to retrieve (e.g., "PTS", "REB", "AST").

        Returns:
            The stat value as a string, or None if not found.

        Example:
            >>> keys = ["MIN", "FG", "3PT", "FT", "REB", "AST", "PTS"]
            >>> stats.get_stat(keys, "PTS")
            '22'
        """
        try:
            index = keys.index(stat_name)
            return self.stats[index] if index < len(self.stats) else None
        except (ValueError, IndexError):
            return None

    def parse_points(self, keys: list[str]) -> int:
        """Parse points scored from the stats array.

        Args:
            keys: List of stat key names matching stats array order.

        Returns:
            Points scored as integer, or 0 if not found/invalid.
        """
        pts = self.get_stat(keys, "PTS")
        return int(pts) if pts and pts.isdigit() else 0

    def parse_rebounds(self, keys: list[str]) -> int:
        """Parse total rebounds from the stats array.

        Args:
            keys: List of stat key names matching stats array order.

        Returns:
            Rebounds as integer, or 0 if not found/invalid.
        """
        reb = self.get_stat(keys, "REB")
        return int(reb) if reb and reb.isdigit() else 0

    def parse_assists(self, keys: list[str]) -> int:
        """Parse assists from the stats array.

        Args:
            keys: List of stat key names matching stats array order.

        Returns:
            Assists as integer, or 0 if not found/invalid.
        """
        ast = self.get_stat(keys, "AST")
        return int(ast) if ast and ast.isdigit() else 0


class ESPNPlayerStatsGroup(BaseModel):
    """Group of player statistics with column keys and labels.

    Contains statistics for all players on a team, along with
    the metadata needed to interpret the stat values.

    Attributes:
        names: Alternative stat category names.
        name: Primary stat category name.
        keys: Short stat keys (e.g., ["MIN", "FG", "3PT", "PTS"]).
        labels: Display labels for each stat column.
        descriptions: Long descriptions for each stat.
        athletes: List of player stats in this category.
        totals: Team total values for each stat column.
    """

    names: list[str] | None = None
    name: str | None = None
    keys: list[str]
    labels: list[str]
    descriptions: list[str] | None = None
    athletes: list[ESPNPlayerStats]
    totals: list[str] | None = None


class ESPNBoxscoreTeam(BaseModel):
    """Team-level box score information.

    Contains team identification and aggregate team statistics
    for a game.

    Attributes:
        team: Basic team identification.
        statistics: List of team-level stat dictionaries.
    """

    team: ESPNTeamBasic
    statistics: list[dict] | None = None


class ESPNBoxscorePlayers(BaseModel):
    """Player statistics for a team in a box score.

    Groups all player statistics by team, with stat keys
    included for parsing.

    Attributes:
        team: The team these players belong to.
        statistics: List of stat groups (usually just one).
    """

    team: ESPNTeamBasic
    statistics: list[ESPNPlayerStatsGroup]


class ESPNBoxscore(BaseModel):
    """Complete game box score with team and player statistics.

    Contains all statistical data for a completed or in-progress
    game, including both team totals and individual player stats.

    Attributes:
        teams: List of team-level statistics (usually 2 teams).
        players: List of player statistics grouped by team.
    """

    teams: list[ESPNBoxscoreTeam]
    players: list[ESPNBoxscorePlayers]


class ESPNCompetitor(BaseModel):
    """A competitor (team) participating in a game.

    Represents one side of a game matchup with scoring
    and outcome information.

    Attributes:
        id: ESPN team identifier.
        homeAway: Either "home" or "away".
        team: Team identification details.
        score: Current or final score as string.
        winner: True if this team won (null if game incomplete).
    """

    id: str
    homeAway: str
    team: ESPNTeamBasic
    score: str | None = None
    winner: bool | None = None


class ESPNCompetition(BaseModel):
    """Competition (game) information from ESPN.

    Contains game metadata and participating teams.

    Attributes:
        id: Unique game identifier.
        date: ISO format datetime string.
        attendance: Number of fans at the game.
        competitors: List of teams (usually exactly 2).
    """

    id: str
    date: str
    attendance: int | None = None
    competitors: list[ESPNCompetitor]


class ESPNGameHeader(BaseModel):
    """Game header with competition details.

    Top-level container for game metadata used in
    game summary responses.

    Attributes:
        id: Game identifier.
        competitions: List of competitions (usually just one).
    """

    id: str
    competitions: list[ESPNCompetition]


class ESPNGameSummary(BaseModel):
    """Complete game summary response from ESPN.

    Contains all data for a single game including header
    information and full box score.

    Attributes:
        header: Game metadata and team information.
        boxscore: Complete player and team statistics.

    Example:
        >>> summary = ESPNGameSummary.model_validate(api_response)
        >>> game_id = summary.header.id
        >>> for player_group in summary.boxscore.players:
        ...     team_name = player_group.team.displayName
    """

    header: ESPNGameHeader
    boxscore: ESPNBoxscore


class ESPNEvent(BaseModel):
    """Event (game) from a scoreboard response.

    Represents a scheduled or completed game as listed
    on the ESPN scoreboard.

    Attributes:
        id: Unique event identifier.
        date: ISO format scheduled datetime.
        name: Full game name (e.g., "Duke at UNC").
        shortName: Abbreviated name (e.g., "DUKE @ UNC").
        competitions: List of competitions in this event.
    """

    id: str
    date: str
    name: str
    shortName: str | None = None
    competitions: list[ESPNCompetition]


class ESPNScoreboard(BaseModel):
    """Scoreboard response containing multiple events.

    Root model for parsing ESPN scoreboard API responses.

    Attributes:
        events: List of games/events on the scoreboard.

    Example:
        >>> scoreboard = ESPNScoreboard.model_validate(api_response)
        >>> for event in scoreboard.events:
        ...     print(f"Game: {event.name}")
    """

    events: list[ESPNEvent]


class ESPNTeamRecord(BaseModel):
    """Team record/standing information.

    Attributes:
        summary: Win-loss record string (e.g., "25-6").
    """

    summary: str | None = None


class ESPNTeamDetail(BaseModel):
    """Detailed team information from team endpoint.

    Contains comprehensive team data including branding
    and performance information.

    Attributes:
        id: ESPN team identifier.
        displayName: Full team name.
        abbreviation: Short team code.
        location: School/city name.
        name: Team mascot/nickname.
        slug: URL-friendly team identifier.
        color: Primary color hex code.
        logos: List of logo image URLs and sizes.
        record: Team record information.
        rank: AP/Coaches poll ranking if ranked.
    """

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
    """Team API response wrapper.

    Attributes:
        team: Detailed team information.
    """

    team: ESPNTeamDetail


class ESPNRosterAthlete(BaseModel):
    """Athlete from roster endpoint with full details.

    Contains comprehensive player information including
    physical attributes and status.

    Attributes:
        id: ESPN player identifier.
        firstName: Player's first name.
        lastName: Player's last name.
        fullName: Complete name (e.g., "John Smith").
        displayName: Formatted display name.
        shortName: Abbreviated name (e.g., "J. Smith").
        jersey: Jersey number.
        position: Position information.
        height: Height in inches.
        displayHeight: Formatted height (e.g., "6'5\"").
        weight: Weight in pounds.
        displayWeight: Formatted weight (e.g., "200 lbs").
        experience: Class year information.
        status: Active/injured status.
    """

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
    """Roster API response with team and players.

    Attributes:
        team: Team identification.
        athletes: List of players on the roster.
        season: Season information.

    Example:
        >>> roster = ESPNRosterResponse.model_validate(api_response)
        >>> for athlete in roster.athletes:
        ...     print(f"{athlete.fullName} #{athlete.jersey}")
    """

    team: ESPNTeamBasic
    athletes: list[ESPNRosterAthlete]
    season: dict | None = None


class ESPNTournamentParticipant(BaseModel):
    """Tournament bracket participant (team with seed).

    Represents a team in the tournament bracket including
    their seed number.

    Attributes:
        id: ESPN team identifier.
        name: Team display name.
        market: School/location name.
        seed: Tournament seed (1-16).
        type: Entity type (always "team").
    """

    id: str
    name: str
    market: str | None = None
    seed: int | None = None
    type: str = "team"


class ESPNTournamentGame(BaseModel):
    """Tournament bracket game placeholder.

    Attributes:
        id: Game identifier.
        scheduled: ISO format scheduled datetime.
    """

    id: str
    scheduled: str | None = None


class ESPNTournamentBracket(BaseModel):
    """Tournament bracket/region information.

    Represents one region of the tournament bracket
    (e.g., East, West, South, Midwest).

    Attributes:
        id: Bracket/region identifier.
        name: Region name (e.g., "East Region").
        location: Regional site location.
        participants: Teams in this bracket with seeds.
        games: Scheduled games in this bracket.
    """

    id: str
    name: str
    location: str | None = None
    participants: list[ESPNTournamentParticipant] = []
    games: list[ESPNTournamentGame] = []


class ESPNTournament(BaseModel):
    """Tournament response with bracket information.

    Root model for tournament bracket API responses.

    Attributes:
        id: Tournament identifier.
        name: Tournament name (e.g., "NCAA Tournament").
        status: Current status (upcoming, in_progress, completed).
        start_date: Tournament start date.
        end_date: Tournament end date.
        brackets: List of regional brackets.

    Example:
        >>> tournament = ESPNTournament.model_validate(api_response)
        >>> for bracket in tournament.brackets:
        ...     for team in bracket.participants:
        ...         print(f"#{team.seed} {team.name}")
    """

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
    """Tournament database model.

    Represents a tournament record in the database, storing
    overall tournament information and status.

    Attributes:
        id: Primary key, typically from ESPN.
        name: Tournament display name.
        year: Tournament year (e.g., 2026).
        status: Tournament status (upcoming, in_progress, completed).
        start_date: Official start date.
        end_date: Official end date.
        raw_data: Original ESPN API response for reference.
        created_at: Record creation timestamp.
        updated_at: Last modification timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    year: int
    status: str = "upcoming"
    start_date: datetime | None = None
    end_date: datetime | None = None
    raw_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Team(BaseModel):
    """Team database model.

    Represents a team participating in the tournament.

    Attributes:
        id: Primary key, ESPN team ID.
        name: Full team display name.
        market: School/location name (e.g., "Duke").
        abbreviation: Short code (e.g., "DUKE").
        seed: Tournament seed 1-16, null for non-tournament.
        year: Season year.
        eliminated: Whether team has been eliminated.
        eliminated_round: Round of elimination if applicable.
        raw_data: Original ESPN data.
        created_at: Record creation timestamp.
        updated_at: Last modification timestamp.

    Example:
        >>> team = Team(
        ...     id="150",
        ...     name="Duke Blue Devils",
        ...     market="Duke",
        ...     seed=1,
        ...     year=2026
        ... )
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    market: str | None = None
    abbreviation: str | None = None
    seed: int | None = None
    year: int
    eliminated: bool = False
    eliminated_round: str | None = None
    raw_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Player(BaseModel):
    """Player database model.

    Represents an individual basketball player.

    Attributes:
        id: Primary key, ESPN player ID.
        team_id: Foreign key to team.
        full_name: Complete player name.
        short_name: Abbreviated name.
        position: Position abbreviation (G, F, C).
        jersey_number: Jersey number as string.
        year: Season year.
        active: Whether player is active on roster.
        raw_data: Original ESPN data.
        created_at: Record creation timestamp.
        updated_at: Last modification timestamp.

    Example:
        >>> player = Player(
        ...     id="12345",
        ...     team_id="150",
        ...     full_name="John Smith",
        ...     position="G",
        ...     jersey_number="23",
        ...     year=2026
        ... )
    """

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
    """Game database model.

    Represents a basketball game between two teams.

    Attributes:
        id: Primary key, ESPN game ID.
        home_team_id: Foreign key to home team.
        away_team_id: Foreign key to away team.
        year: Season year.
        round_name: Tournament round name.
        scheduled_date: Game start time.
        status: Game status (scheduled, in_progress, completed, cancelled).
        home_score: Home team final score.
        away_score: Away team final score.
        winner_team_id: ID of winning team.
        raw_data: Original ESPN data.
        created_at: Record creation timestamp.
        updated_at: Last modification timestamp.

    Example:
        >>> game = Game(
        ...     id="401234567",
        ...     home_team_id="150",
        ...     away_team_id="153",
        ...     year=2026,
        ...     round_name="Round of 64"
        ... )
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    home_team_id: str
    away_team_id: str
    year: int
    round_name: str | None = None
    scheduled_date: datetime | None = None
    status: str = "scheduled"
    home_score: int | None = None
    away_score: int | None = None
    winner_team_id: str | None = None
    raw_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PlayerGameStats(BaseModel):
    """Player game statistics database model.

    Stores individual player performance for a single game.
    This is the core data used for pool scoring.

    Attributes:
        id: Auto-incremented primary key.
        game_id: Foreign key to game.
        player_id: Foreign key to player.
        team_id: Foreign key to team.
        year: Season year.
        points: Points scored.
        rebounds: Total rebounds.
        assists: Assists.
        minutes_played: Minutes played.
        field_goals_made: Field goals made.
        field_goals_attempted: Field goal attempts.
        three_pointers_made: Three-pointers made.
        three_pointers_attempted: Three-point attempts.
        free_throws_made: Free throws made.
        free_throws_attempted: Free throw attempts.
        steals: Steals.
        blocks: Blocks.
        turnovers: Turnovers.
        fouls: Personal fouls.
        starter: Whether player started.
        did_not_play: Whether player was DNP.
        raw_data: Original ESPN data.
        created_at: Record creation timestamp.
        updated_at: Last modification timestamp.

    Example:
        >>> stats = PlayerGameStats(
        ...     game_id="401234567",
        ...     player_id="12345",
        ...     team_id="150",
        ...     year=2026,
        ...     points=22,
        ...     rebounds=7,
        ...     assists=3
        ... )
        >>> stats.total_score
        32
    """

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
        """Calculate total score for pool scoring.

        The pool uses Points + Rebounds + Assists as the
        scoring formula.

        Returns:
            Combined total of points, rebounds, and assists.

        Example:
            >>> stats = PlayerGameStats(points=22, rebounds=7, assists=3, ...)
            >>> stats.total_score
            32
        """
        return self.points + self.rebounds + self.assists


# ============================================
# View Models for Google Sheets Export
# ============================================


class PlayerExport(BaseModel):
    """Player data formatted for Google Sheets export.

    Flattened view of player data including team information
    for easy export to spreadsheets.

    Attributes:
        player_id: Player identifier.
        player_name: Full player name.
        position: Position abbreviation.
        jersey_number: Jersey number.
        team_id: Team identifier.
        team_name: Team display name.
        seed: Tournament seed.
        eliminated: Team elimination status.
        tournament_year: Year of tournament.
        active: Player roster status.
    """

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
    """Aggregated player tournament statistics for export.

    Summarizes a player's total tournament performance
    across all games played.

    Attributes:
        player_id: Player identifier.
        player_name: Full player name.
        team_name: Team display name.
        seed: Tournament seed.
        tournament_year: Year of tournament.
        games_played: Number of games with stats.
        total_points: Sum of points across all games.
        total_rebounds: Sum of rebounds across all games.
        total_assists: Sum of assists across all games.
        total_score: Pool score (PTS + REB + AST).
        avg_points: Points per game average.
        avg_rebounds: Rebounds per game average.
        avg_assists: Assists per game average.
        eliminated: Team elimination status.
    """

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
    """Game-by-game player statistics for export.

    Detailed per-game statistics with game context
    for comprehensive analysis.

    Attributes:
        game_id: Game identifier.
        tournament_year: Year of tournament.
        round_name: Tournament round.
        scheduled_date: Game date/time.
        game_status: Game completion status.
        home_team: Home team name.
        away_team: Away team name.
        home_score: Home team score.
        away_score: Away team score.
        player_name: Player name.
        player_team: Player's team name.
        seed: Player's team seed.
        points: Points in this game.
        rebounds: Rebounds in this game.
        assists: Assists in this game.
        total_score: Pool score for this game.
        minutes_played: Minutes played.
    """

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
