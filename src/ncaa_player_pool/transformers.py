"""Data transformation utilities for ESPN API responses.

This module provides functions to transform raw ESPN API responses into
structured Pydantic models suitable for database storage. It handles
the mapping between ESPN's data format and the application's domain models.

The transformation functions:

- Parse ESPN date formats to Python datetime objects
- Extract team and player information from nested API responses
- Convert box score statistics to PlayerGameStats models
- Handle tournament bracket data with seed information

Example:
    Transform a roster response::

        from ncaa_player_pool.transformers import transform_roster_to_players
        from ncaa_player_pool.models import ESPNRosterResponse

        roster = ESPNRosterResponse.model_validate(api_response)
        team, players = transform_roster_to_players(roster, year=2026)
        print(f"Team: {team.name}, Players: {len(players)}")

    Transform game summary to player stats::

        from ncaa_player_pool.transformers import transform_game_summary_to_player_stats
        from ncaa_player_pool.models import ESPNGameSummary

        summary = ESPNGameSummary.model_validate(api_response)
        players, stats = transform_game_summary_to_player_stats(summary, year=2026)

Attributes:
    logger: Module-level logger for transformation operations.

Functions:
    parse_espn_date: Parse ESPN ISO date strings to datetime.
    extract_year_from_date: Extract year from date string with fallback.
    transform_roster_to_players: Convert roster response to Team and Players.
    transform_scoreboard_to_games: Convert scoreboard to Game models.
    transform_scoreboard_to_teams: Convert scoreboard to Team models.
    transform_game_summary_to_player_stats: Convert game summary to stats.
    transform_game_summary_to_game: Convert game summary to Game model.
    transform_tournament_to_teams: Convert tournament bracket to Teams.
    transform_tournament_to_tournament: Convert to Tournament model.
"""

from datetime import datetime

from .logger import get_logger
from .models import (
    ESPNGameSummary,
    ESPNRosterResponse,
    ESPNScoreboard,
    ESPNTournament,
    Game,
    Player,
    PlayerGameStats,
    Team,
    Tournament,
)

logger = get_logger(__name__)


def parse_espn_date(date_str: str) -> datetime | None:
    """Parse ESPN date string to Python datetime.

    ESPN dates are typically in ISO 8601 format with 'Z' suffix
    for UTC timezone (e.g., "2026-03-19T01:00Z").

    Args:
        date_str: Date string from ESPN API in ISO format.

    Returns:
        Timezone-aware datetime object, or None if the string is
        empty or cannot be parsed.

    Example:
        Parse a game date::

            dt = parse_espn_date("2026-03-19T19:00Z")
            print(dt.year, dt.month, dt.day)  # 2026 3 19
    """
    if not date_str:
        return None

    try:
        # ESPN dates are typically in ISO format: "2026-01-19T01:00Z"
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def extract_year_from_date(date_str: str | None, default_year: int) -> int:
    """Extract year from ESPN date string with fallback.

    Attempts to parse the date string and extract the year. If parsing
    fails or the string is None/empty, returns the default year.

    Args:
        date_str: Date string in ESPN format, or None.
        default_year: Year to return if extraction fails.

    Returns:
        Extracted year as integer, or default_year on failure.

    Example:
        Extract tournament year::

            year = extract_year_from_date("2026-03-19T19:00Z", 2025)
            print(year)  # 2026
    """
    if date_str:
        dt = parse_espn_date(date_str)
        if dt:
            return dt.year
    return default_year


def transform_roster_to_players(
    roster: ESPNRosterResponse,
    year: int,
    seed: int | None = None,
) -> tuple[Team, list[Player]]:
    """Transform ESPN roster response into Team and Player models.

    Extracts team information and creates a Team model, then iterates
    through all athletes to create Player models.

    Args:
        roster: Validated ESPN roster response containing team and
            athletes data.
        year: Tournament/season year for the team and players.
        seed: Optional tournament seed (1-16) for the team.

    Returns:
        A tuple containing:
            - Team: The team model with all team information
            - list[Player]: List of player models for all roster athletes

    Example:
        Process a roster response::

            roster = ESPNRosterResponse.model_validate(api_response)
            team, players = transform_roster_to_players(roster, 2026, seed=1)
            print(f"{team.name}: {len(players)} players")
    """
    # Create team model
    team = Team(
        id=roster.team.id,
        name=roster.team.name or roster.team.displayName,
        market=roster.team.location,
        abbreviation=roster.team.abbreviation,
        seed=seed,
        year=year,
        eliminated=False,
        raw_data=roster.team.model_dump(),
    )

    # Create player models
    players = []
    for athlete in roster.athletes:
        player = Player(
            id=athlete.id,
            team_id=roster.team.id,
            full_name=athlete.fullName,
            short_name=athlete.shortName,
            position=athlete.position.abbreviation if athlete.position else None,
            jersey_number=athlete.jersey,
            year=year,
            active=True,
            raw_data=athlete.model_dump(),
        )
        players.append(player)

    logger.info(f"Transformed roster: {team.name} with {len(players)} players")
    return team, players


def transform_scoreboard_to_games(scoreboard: ESPNScoreboard, year: int) -> list[Game]:
    """Transform ESPN scoreboard into Game models.

    Parses scoreboard events and their competitions to create Game
    models with home/away teams, scores, and game status.

    Args:
        scoreboard: Validated ESPN scoreboard response containing
            events and competitions.
        year: Tournament/season year for the games.

    Returns:
        List of Game models, one for each competition in the scoreboard.
        Games missing home or away team data are skipped with a warning.

    Example:
        Get games from today's scoreboard::

            scoreboard = ESPNScoreboard.model_validate(api_response)
            games = transform_scoreboard_to_games(scoreboard, 2026)
            for game in games:
                print(f"Game {game.id}: {game.home_score}-{game.away_score}")
    """
    games = []

    for event in scoreboard.events:
        for competition in event.competitions:
            # Determine home/away teams
            home_team = None
            away_team = None

            for competitor in competition.competitors:
                if competitor.homeAway == "home":
                    home_team = competitor
                elif competitor.homeAway == "away":
                    away_team = competitor

            if not home_team or not away_team:
                logger.warning(f"Missing home/away team for game {event.id}")
                continue

            # Determine winner
            winner_id = None
            if home_team.winner:
                winner_id = home_team.id
            elif away_team.winner:
                winner_id = away_team.id

            # Parse scores
            home_score = int(home_team.score) if home_team.score and home_team.score.isdigit() else None
            away_score = int(away_team.score) if away_team.score and away_team.score.isdigit() else None

            game = Game(
                id=event.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                year=year,
                scheduled_date=parse_espn_date(competition.date),
                status="completed" if winner_id else "in_progress",
                home_score=home_score,
                away_score=away_score,
                winner_team_id=winner_id,
                raw_data=event.model_dump(),
            )

            games.append(game)

    logger.info(f"Transformed {len(games)} games from scoreboard")
    return games


def transform_scoreboard_to_teams(scoreboard: ESPNScoreboard, year: int) -> list[Team]:
    """Transform ESPN scoreboard into unique Team models.

    Extracts all teams participating in scoreboard games and creates
    Team models. Deduplicates teams that appear in multiple games.

    Args:
        scoreboard: Validated ESPN scoreboard response containing
            events and competitions with team data.
        year: Tournament/season year for the teams.

    Returns:
        List of unique Team models. Each team appears only once
        regardless of how many games they're in.

    Note:
        Teams extracted from scoreboard don't have seed information.
        Use transform_tournament_to_teams for seeded teams.
    """
    teams_dict = {}

    for event in scoreboard.events:
        for competition in event.competitions:
            for competitor in competition.competitors:
                team_id = competitor.id

                if team_id not in teams_dict:
                    team = Team(
                        id=team_id,
                        name=competitor.team.name or competitor.team.displayName,
                        market=competitor.team.location,
                        abbreviation=competitor.team.abbreviation,
                        seed=None,  # Seeds only available in tournament bracket
                        year=year,
                        eliminated=False,
                        raw_data=competitor.team.model_dump(),
                    )
                    teams_dict[team_id] = team

    teams = list(teams_dict.values())
    logger.info(f"Transformed {len(teams)} unique teams from scoreboard")
    return teams


def parse_stat_value(value: str) -> int | None:
    """Parse basketball statistic value from string.

    Handles two common ESPN stat formats:
    - Simple integer: "21" -> 21
    - Made-attempted: "2-6" -> 2 (returns made count)

    Args:
        value: Stat value as string from ESPN box score.

    Returns:
        Parsed integer value, or None if the value is empty
        or cannot be parsed.

    Example:
        Parse various stat formats::

            parse_stat_value("21")    # 21 (points)
            parse_stat_value("5-10")  # 5 (field goals made)
            parse_stat_value("")      # None
    """
    if not value:
        return None

    # Handle "made-attempted" format (e.g., "2-6")
    if "-" in value:
        parts = value.split("-")
        if parts[0].isdigit():
            return int(parts[0])  # Return made count
        return None

    # Handle simple integer
    if value.isdigit():
        return int(value)

    return None


def transform_game_summary_to_player_stats(
    game_summary: ESPNGameSummary,
    year: int,
) -> tuple[list[Player], list[PlayerGameStats]]:
    """Transform ESPN game summary into Player and PlayerGameStats models.

    Parses the boxscore section of a game summary to extract all player
    statistics. Creates both Player models (for roster tracking) and
    PlayerGameStats models (for box score data).

    Args:
        game_summary: Validated ESPN game summary containing boxscore
            with player statistics.
        year: Tournament/season year for the records.

    Returns:
        A tuple containing:
            - list[Player]: Player models for all athletes in the game
            - list[PlayerGameStats]: Statistics for each player

    Note:
        The ESPN API uses two stat formats - uppercase abbreviations
        (PTS, REB, AST) or lowercase names. This function handles both.

    Example:
        Process game statistics::

            summary = ESPNGameSummary.model_validate(api_response)
            players, stats = transform_game_summary_to_player_stats(summary, 2026)
            for player, stat in zip(players, stats):
                print(f"{player.full_name}: {stat.points} pts")
    """
    players = []
    stats_list = []

    for team_players in game_summary.boxscore.players:
        team_id = team_players.team.id

        for stats_group in team_players.statistics:
            keys = stats_group.keys

            for athlete_stats in stats_group.athletes:
                athlete = athlete_stats.athlete

                # Create Player model
                player = Player(
                    id=athlete.id,
                    team_id=team_id,
                    full_name=athlete.displayName,
                    short_name=athlete.shortName,
                    position=athlete.position.abbreviation if athlete.position else None,
                    jersey_number=athlete.jersey,
                    year=year,
                    active=True,
                    raw_data=athlete.model_dump(),
                )
                players.append(player)

                # Parse individual stats
                stats_array = athlete_stats.stats

                # Helper to get stat by key name (handles both formats)
                def get_stat(*possible_keys: str) -> int | None:
                    for key in possible_keys:
                        try:
                            idx = keys.index(key)
                            return parse_stat_value(stats_array[idx]) if idx < len(stats_array) else None
                        except (ValueError, IndexError):
                            continue
                    return None

                # Create PlayerGameStats model
                # ESPN API has two formats: uppercase abbreviations (PTS, REB, AST) or lowercase names (points, rebounds, assists)
                player_stats = PlayerGameStats(
                    game_id=game_summary.header.id,
                    player_id=athlete.id,
                    team_id=team_id,
                    year=year,
                    points=get_stat("PTS", "points") or 0,
                    rebounds=get_stat("REB", "rebounds") or 0,
                    assists=get_stat("AST", "assists") or 0,
                    minutes_played=get_stat("MIN", "minutes"),
                    field_goals_made=get_stat("FG", "fieldGoalsMade-fieldGoalsAttempted"),
                    three_pointers_made=get_stat("3PT", "threePointFieldGoalsMade-threePointFieldGoalsAttempted"),
                    free_throws_made=get_stat("FT", "freeThrowsMade-freeThrowsAttempted"),
                    steals=get_stat("STL", "steals"),
                    blocks=get_stat("BLK", "blocks"),
                    turnovers=get_stat("TO", "turnovers"),
                    fouls=get_stat("PF", "fouls"),
                    starter=athlete_stats.starter,
                    did_not_play=athlete_stats.didNotPlay,
                    raw_data=athlete_stats.model_dump(),
                )
                stats_list.append(player_stats)

    logger.info(f"Transformed {len(players)} players and {len(stats_list)} stat records from game summary")
    return players, stats_list


def transform_game_summary_to_game(game_summary: ESPNGameSummary, year: int) -> Game:
    """Transform ESPN game summary into Game model.

    Extracts game header information to create a Game model with
    final scores, winner, and scheduling information.

    Args:
        game_summary: Validated ESPN game summary containing header
            with competition details.
        year: Tournament/season year for the game.

    Returns:
        Game model with complete game information.

    Raises:
        ValueError: If the game is missing home or away team data.
    """
    competition = game_summary.header.competitions[0]

    # Determine home/away teams
    home_team = None
    away_team = None

    for competitor in competition.competitors:
        if competitor.homeAway == "home":
            home_team = competitor
        elif competitor.homeAway == "away":
            away_team = competitor

    if not home_team or not away_team:
        raise ValueError(f"Missing home/away team in game {game_summary.header.id}")

    # Determine winner
    winner_id = None
    if home_team.winner:
        winner_id = home_team.id
    elif away_team.winner:
        winner_id = away_team.id

    # Parse scores
    home_score = int(home_team.score) if home_team.score and home_team.score.isdigit() else None
    away_score = int(away_team.score) if away_team.score and away_team.score.isdigit() else None

    game = Game(
        id=game_summary.header.id,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        year=year,
        scheduled_date=parse_espn_date(competition.date),
        status="completed" if winner_id else "in_progress",
        home_score=home_score,
        away_score=away_score,
        winner_team_id=winner_id,
        raw_data=game_summary.header.model_dump(),
    )

    logger.debug(f"Transformed game {game.id}")
    return game


def transform_tournament_to_teams(tournament: ESPNTournament, year: int) -> list[Team]:
    """Transform ESPN tournament bracket into Team models with seeds.

    Parses tournament brackets to extract all participating teams
    with their seed information. This is the primary way to get
    seeded team data.

    Args:
        tournament: Validated ESPN tournament response containing
            brackets with participants.
        year: Tournament year for the teams.

    Returns:
        List of unique Team models with seed information populated.

    Example:
        Get all seeded teams::

            tournament = ESPNTournament.model_validate(api_response)
            teams = transform_tournament_to_teams(tournament, 2026)
            for team in sorted(teams, key=lambda t: t.seed or 99):
                print(f"#{team.seed} {team.name}")
    """
    teams_dict = {}

    for bracket in tournament.brackets:
        for participant in bracket.participants:
            team_id = participant.id

            if team_id not in teams_dict:
                team = Team(
                    id=team_id,
                    name=participant.name,
                    market=participant.market,
                    abbreviation=None,
                    seed=participant.seed,
                    year=year,
                    eliminated=False,
                    raw_data=participant.model_dump(),
                )
                teams_dict[team_id] = team

    teams = list(teams_dict.values())
    logger.info(f"Transformed {len(teams)} tournament teams with seeds")
    return teams


def transform_tournament_to_tournament(tournament: ESPNTournament) -> Tournament:
    """Transform ESPN tournament data into Tournament model.

    Creates a Tournament model with metadata about the tournament
    including name, year, status, and date range.

    Args:
        tournament: Validated ESPN tournament response.

    Returns:
        Tournament model with all tournament metadata.

    Example:
        Create tournament record::

            tournament_data = ESPNTournament.model_validate(api_response)
            tournament = transform_tournament_to_tournament(tournament_data)
            print(f"{tournament.name} ({tournament.year})")
    """
    start_date = parse_espn_date(tournament.start_date) if tournament.start_date else None
    end_date = parse_espn_date(tournament.end_date) if tournament.end_date else None

    year = start_date.year if start_date else datetime.now().year

    tournament_model = Tournament(
        id=tournament.id,
        name=tournament.name,
        year=year,
        status=tournament.status,
        start_date=start_date,
        end_date=end_date,
        raw_data=tournament.model_dump(),
    )

    logger.info(f"Transformed tournament: {tournament_model.name} ({tournament_model.year})")
    return tournament_model
