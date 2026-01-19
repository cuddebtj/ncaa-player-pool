"""
Data transformation utilities.
Converts ESPN API responses into database models.
"""

from datetime import datetime
from typing import List, Optional, Tuple
import pytz

from logger import get_logger
from models import (
    # ESPN Models
    ESPNGameSummary,
    ESPNScoreboard,
    ESPNTournament,
    ESPNTeamResponse,
    ESPNRosterResponse,
    ESPNBoxscorePlayers,
    ESPNPlayerStats,
    # Database Models
    Tournament,
    Team,
    Player,
    Game,
    PlayerGameStats,
)

logger = get_logger(__name__)


def parse_espn_date(date_str: str) -> Optional[datetime]:
    """
    Parse ESPN date string to datetime.

    Args:
        date_str: Date string from ESPN API (ISO format)

    Returns:
        Datetime object or None if parsing fails
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


def extract_year_from_date(date_str: Optional[str], default_year: int) -> int:
    """
    Extract year from date string.

    Args:
        date_str: Date string
        default_year: Default year if extraction fails

    Returns:
        Year as integer
    """
    if date_str:
        dt = parse_espn_date(date_str)
        if dt:
            return dt.year
    return default_year


def transform_roster_to_players(
    roster: ESPNRosterResponse,
    year: int,
    seed: Optional[int] = None,
) -> Tuple[Team, List[Player]]:
    """
    Transform ESPN roster response into Team and Player models.

    Args:
        roster: ESPN roster response
        year: Tournament/season year
        seed: Optional tournament seed

    Returns:
        Tuple of (team model, list of player models)
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


def transform_scoreboard_to_games(scoreboard: ESPNScoreboard, year: int) -> List[Game]:
    """
    Transform ESPN scoreboard into Game models.

    Args:
        scoreboard: ESPN scoreboard response
        year: Tournament/season year

    Returns:
        List of Game models
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


def transform_scoreboard_to_teams(scoreboard: ESPNScoreboard, year: int) -> List[Team]:
    """
    Transform ESPN scoreboard into Team models.

    Args:
        scoreboard: ESPN scoreboard response
        year: Tournament/season year

    Returns:
        List of unique Team models
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


def parse_stat_value(value: str) -> Optional[int]:
    """
    Parse stat value from string, handling formats like "2-6" or "21".

    Args:
        value: Stat value as string

    Returns:
        Integer value or None
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
) -> Tuple[List[Player], List[PlayerGameStats]]:
    """
    Transform ESPN game summary into Player and PlayerGameStats models.

    Args:
        game_summary: ESPN game summary response
        year: Tournament/season year

    Returns:
        Tuple of (players list, player_stats list)
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
                def get_stat(*possible_keys: str) -> Optional[int]:
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
    """
    Transform ESPN game summary into Game model.

    Args:
        game_summary: ESPN game summary response
        year: Tournament/season year

    Returns:
        Game model
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


def transform_tournament_to_teams(tournament: ESPNTournament, year: int) -> List[Team]:
    """
    Transform ESPN tournament bracket into Team models with seeds.

    Args:
        tournament: ESPN tournament response
        year: Tournament year

    Returns:
        List of Team models with seed information
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
    """
    Transform ESPN tournament into Tournament model.

    Args:
        tournament: ESPN tournament response

    Returns:
        Tournament model
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
