"""PostgreSQL database operations for NCAA Player Pool.

This module provides database connectivity and CRUD operations for storing
tournament data, team rosters, player information, and game statistics.
It uses psycopg (psycopg3) for PostgreSQL connections.

Example:
    Basic usage with context manager::

        from ncaa_player_pool.db import Database
        from ncaa_player_pool.config import get_config

        config = get_config()

        with Database(config) as db:
            # Insert a team
            db.upsert_team(team)

            # Get export data
            players = db.get_players_export(year=2026)

    Running migrations::

        with Database(config) as db:
            db.run_migration(Path("migrations/001_initial_schema.sql"))

Attributes:
    logger: Module-level logger instance for database operations.

Note:
    The database schema uses PostgreSQL-specific features like JSONB columns
    for storing raw API responses and ON CONFLICT for upsert operations.
"""

from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql

from .config import Config
from .logger import get_logger
from .models import (
    Game,
    Player,
    PlayerGameStats,
    Team,
    Tournament,
)

logger = get_logger(__name__)


class Database:
    """PostgreSQL database connection and operations manager.

    Provides methods for connecting to PostgreSQL, running migrations,
    and performing CRUD operations on tournament-related tables. Supports
    both manual connection management and context manager usage.

    Attributes:
        config: Application configuration with database credentials.
        conn: Active database connection, or None if not connected.

    Example:
        Using as context manager (recommended)::

            with Database(config) as db:
                db.upsert_team(team)
                db.upsert_player(player)
            # Connection automatically closed and committed

        Manual connection management::

            db = Database(config)
            try:
                db.connect()
                db.upsert_team(team)
                db.conn.commit()
            finally:
                db.close()
    """

    def __init__(self, config: Config):
        """Initialize database manager with configuration.

        Args:
            config: Application configuration containing PostgreSQL
                connection string and schema settings.
        """
        self.config = config
        self.conn: psycopg.Connection | None = None

    def connect(self) -> psycopg.Connection:
        """Establish connection to PostgreSQL database.

        Creates a new connection if one doesn't exist or if the existing
        connection is closed. Also sets the search_path to include the
        configured schema.

        Returns:
            Active database connection object.

        Raises:
            psycopg.DatabaseError: If connection fails due to invalid
                credentials, network issues, or database unavailability.

        Example:
            Manual connection::

                db = Database(config)
                conn = db.connect()
                # Use conn for custom queries
        """
        if self.conn is None or self.conn.closed:
            try:
                self.conn = psycopg.connect(self.config.postgres_conn_str)
                logger.info("Database connection established")

                # Set search path to schema
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("SET search_path TO {}, public").format(sql.Identifier(self.config.database_schema))
                    )
                    self.conn.commit()

            except psycopg.DatabaseError as e:
                logger.exception(f"Database connection error: {e}")
                raise

        return self.conn

    def close(self) -> None:
        """Close the database connection.

        Safely closes the connection if it exists and is open.
        Can be called multiple times without error.
        """
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self) -> "Database":
        """Enter context manager and establish connection.

        Returns:
            Self reference for use in with statements.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager with automatic commit or rollback.

        Commits the transaction if no exception occurred, otherwise
        rolls back. Always closes the connection.

        Args:
            exc_type: Exception type if an error occurred, None otherwise.
            exc_val: Exception value if an error occurred, None otherwise.
            exc_tb: Exception traceback if an error occurred, None otherwise.
        """
        if exc_type:
            logger.error(f"Database transaction error: {exc_val}")
            if self.conn:
                self.conn.rollback()
        else:
            if self.conn:
                self.conn.commit()
        self.close()

    def run_migration(self, migration_file: Path) -> None:
        """Execute a SQL migration file against the database.

        Reads the SQL file and executes its contents as a single
        transaction. On failure, the transaction is rolled back.

        Args:
            migration_file: Path to the SQL file containing migration
                statements (CREATE TABLE, ALTER TABLE, etc.).

        Raises:
            FileNotFoundError: If the migration file doesn't exist.
            psycopg.DatabaseError: If any SQL statement fails to execute.

        Example:
            Run initial schema migration::

                with Database(config) as db:
                    db.run_migration(Path("migrations/001_initial_schema.sql"))
        """
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")

        logger.info(f"Running migration: {migration_file.name}")

        try:
            with open(migration_file) as f:
                sql_content = f.read()

            with self.conn.cursor() as cur:
                cur.execute(sql_content)

            self.conn.commit()
            logger.info(f"Migration completed successfully: {migration_file.name}")

        except psycopg.DatabaseError as e:
            logger.exception(f"Migration failed: {e}")
            self.conn.rollback()
            raise

    def upsert_tournament(self, tournament: Tournament) -> None:
        """Insert or update a tournament record.

        Uses PostgreSQL ON CONFLICT to perform an upsert operation.
        If a tournament with the same year and name exists, updates
        the existing record.

        Args:
            tournament: Tournament model instance containing tournament
                details including id, name, year, status, and dates.

        Note:
            The unique constraint is on (year, name), allowing multiple
            tournaments per year with different names.
        """
        query = """
            INSERT INTO tournaments (id, name, year, status, start_date, end_date, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (year, name)
            DO UPDATE SET
                status = EXCLUDED.status,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                raw_data = EXCLUDED.raw_data,
                updated_at = CURRENT_TIMESTAMP
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    tournament.id,
                    tournament.name,
                    tournament.year,
                    tournament.status,
                    tournament.start_date,
                    tournament.end_date,
                    psycopg.types.json.Jsonb(tournament.raw_data) if tournament.raw_data else None,
                ),
            )

        logger.debug(f"Upserted tournament: {tournament.name} ({tournament.year})")

    def upsert_team(self, team: Team) -> None:
        """Insert or update a team record.

        Uses PostgreSQL ON CONFLICT to perform an upsert operation.
        If a team with the same id and year exists, updates the
        existing record including seed and elimination status.

        Args:
            team: Team model instance containing team details including
                id, name, abbreviation, seed, and elimination status.

        Note:
            The unique constraint is on (id, year), allowing the same
            team to appear in multiple tournament years.
        """
        query = """
            INSERT INTO teams (id, name, market, abbreviation, seed, year, eliminated, eliminated_round, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id, year)
            DO UPDATE SET
                name = EXCLUDED.name,
                market = EXCLUDED.market,
                abbreviation = EXCLUDED.abbreviation,
                seed = EXCLUDED.seed,
                eliminated = EXCLUDED.eliminated,
                eliminated_round = EXCLUDED.eliminated_round,
                raw_data = EXCLUDED.raw_data,
                updated_at = CURRENT_TIMESTAMP
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    team.id,
                    team.name,
                    team.market,
                    team.abbreviation,
                    team.seed,
                    team.year,
                    team.eliminated,
                    team.eliminated_round,
                    psycopg.types.json.Jsonb(team.raw_data) if team.raw_data else None,
                ),
            )

        logger.debug(f"Upserted team: {team.name} ({team.year})")

    def upsert_player(self, player: Player) -> None:
        """Insert or update a player record.

        Uses PostgreSQL ON CONFLICT to perform an upsert operation.
        If a player with the same id and year exists, updates the
        existing record.

        Args:
            player: Player model instance containing player details
                including id, team_id, name, position, and jersey number.

        Note:
            The unique constraint is on (id, year), allowing a player's
            information to be stored separately for each tournament year.
        """
        query = """
            INSERT INTO players (id, team_id, full_name, short_name, position, jersey_number, year, active, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id, year)
            DO UPDATE SET
                team_id = EXCLUDED.team_id,
                full_name = EXCLUDED.full_name,
                short_name = EXCLUDED.short_name,
                position = EXCLUDED.position,
                jersey_number = EXCLUDED.jersey_number,
                active = EXCLUDED.active,
                raw_data = EXCLUDED.raw_data,
                updated_at = CURRENT_TIMESTAMP
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    player.id,
                    player.team_id,
                    player.full_name,
                    player.short_name,
                    player.position,
                    player.jersey_number,
                    player.year,
                    player.active,
                    psycopg.types.json.Jsonb(player.raw_data) if player.raw_data else None,
                ),
            )

        logger.debug(f"Upserted player: {player.full_name} ({player.year})")

    def upsert_game(self, game: Game) -> None:
        """Insert or update a game record.

        Uses PostgreSQL ON CONFLICT to perform an upsert operation.
        If a game with the same id and year exists, updates the
        existing record including scores and winner.

        Args:
            game: Game model instance containing game details including
                id, team ids, scores, status, and scheduled date.

        Note:
            The unique constraint is on (id, year), allowing the same
            game id to be used across different tournament years.
        """
        query = """
            INSERT INTO games (id, home_team_id, away_team_id, year, round_name, scheduled_date,
                             status, home_score, away_score, winner_team_id, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id, year)
            DO UPDATE SET
                home_team_id = EXCLUDED.home_team_id,
                away_team_id = EXCLUDED.away_team_id,
                round_name = EXCLUDED.round_name,
                scheduled_date = EXCLUDED.scheduled_date,
                status = EXCLUDED.status,
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score,
                winner_team_id = EXCLUDED.winner_team_id,
                raw_data = EXCLUDED.raw_data,
                updated_at = CURRENT_TIMESTAMP
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    game.id,
                    game.home_team_id,
                    game.away_team_id,
                    game.year,
                    game.round_name,
                    game.scheduled_date,
                    game.status,
                    game.home_score,
                    game.away_score,
                    game.winner_team_id,
                    psycopg.types.json.Jsonb(game.raw_data) if game.raw_data else None,
                ),
            )

        logger.debug(f"Upserted game: {game.id} ({game.year})")

    def upsert_player_game_stats(self, stats: PlayerGameStats) -> None:
        """Insert or update player game statistics.

        Uses PostgreSQL ON CONFLICT to perform an upsert operation.
        If stats for the same game, player, and year exist, updates
        the existing record with new statistics.

        Args:
            stats: PlayerGameStats model instance containing game
                statistics including points, rebounds, assists, and
                other box score data.

        Note:
            The unique constraint is on (game_id, player_id, year),
            ensuring one stats record per player per game per year.
        """
        query = """
            INSERT INTO player_game_stats (
                game_id, player_id, team_id, year,
                points, rebounds, assists,
                minutes_played, field_goals_made, field_goals_attempted,
                three_pointers_made, three_pointers_attempted,
                free_throws_made, free_throws_attempted,
                steals, blocks, turnovers, fouls,
                starter, did_not_play, raw_data
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_id, player_id, year)
            DO UPDATE SET
                team_id = EXCLUDED.team_id,
                points = EXCLUDED.points,
                rebounds = EXCLUDED.rebounds,
                assists = EXCLUDED.assists,
                minutes_played = EXCLUDED.minutes_played,
                field_goals_made = EXCLUDED.field_goals_made,
                field_goals_attempted = EXCLUDED.field_goals_attempted,
                three_pointers_made = EXCLUDED.three_pointers_made,
                three_pointers_attempted = EXCLUDED.three_pointers_attempted,
                free_throws_made = EXCLUDED.free_throws_made,
                free_throws_attempted = EXCLUDED.free_throws_attempted,
                steals = EXCLUDED.steals,
                blocks = EXCLUDED.blocks,
                turnovers = EXCLUDED.turnovers,
                fouls = EXCLUDED.fouls,
                starter = EXCLUDED.starter,
                did_not_play = EXCLUDED.did_not_play,
                raw_data = EXCLUDED.raw_data,
                updated_at = CURRENT_TIMESTAMP
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    stats.game_id,
                    stats.player_id,
                    stats.team_id,
                    stats.year,
                    stats.points,
                    stats.rebounds,
                    stats.assists,
                    stats.minutes_played,
                    stats.field_goals_made,
                    stats.field_goals_attempted,
                    stats.three_pointers_made,
                    stats.three_pointers_attempted,
                    stats.free_throws_made,
                    stats.free_throws_attempted,
                    stats.steals,
                    stats.blocks,
                    stats.turnovers,
                    stats.fouls,
                    stats.starter,
                    stats.did_not_play,
                    psycopg.types.json.Jsonb(stats.raw_data) if stats.raw_data else None,
                ),
            )

        logger.debug(f"Upserted player stats: {stats.player_id} in game {stats.game_id}")

    def get_players_export(self, year: int) -> list[dict[str, Any]]:
        """Retrieve player roster data formatted for export.

        Queries the v_players_export view to get player information
        suitable for Google Sheets export, including player name,
        team, position, and seed.

        Args:
            year: Tournament year to filter players.

        Returns:
            List of dictionaries, each containing player export data
            with keys like player_id, player_name, team_name, position,
            and seed.

        Example:
            Export players for 2026 tournament::

                with Database(config) as db:
                    players = db.get_players_export(2026)
                    for player in players:
                        print(f"{player['player_name']} - {player['team_name']}")
        """
        query = "SELECT * FROM v_players_export WHERE tournament_year = %s"

        with self.conn.cursor() as cur:
            cur.execute(query, (year,))
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

        logger.info(f"Fetched {len(results)} players for export (year: {year})")
        return results

    def get_player_stats_export(self, year: int) -> list[dict[str, Any]]:
        """Retrieve aggregated player statistics for export.

        Queries the v_player_stats_export view to get player statistics
        aggregated across all tournament games, including totals for
        points, rebounds, assists, and computed total score.

        Args:
            year: Tournament year to filter statistics.

        Returns:
            List of dictionaries containing aggregated player stats
            with keys like player_id, player_name, team_name, seed,
            games_played, total_points, total_rebounds, total_assists,
            and total_score.

        Example:
            Get top scorers for leaderboard::

                with Database(config) as db:
                    stats = db.get_player_stats_export(2026)
                    top_scorers = sorted(
                        stats,
                        key=lambda x: x['total_score'],
                        reverse=True
                    )[:10]
        """
        query = "SELECT * FROM v_player_stats_export WHERE tournament_year = %s"

        with self.conn.cursor() as cur:
            cur.execute(query, (year,))
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

        logger.info(f"Fetched stats for {len(results)} players (year: {year})")
        return results

    def get_game_stats_export(self, year: int) -> list[dict[str, Any]]:
        """Retrieve detailed game-by-game player statistics for export.

        Queries the v_game_stats_export view to get individual game
        statistics for each player, including game details and all
        box score statistics.

        Args:
            year: Tournament year to filter statistics.

        Returns:
            List of dictionaries containing per-game player stats
            with keys like player_id, player_name, game_id, round_name,
            home_team, away_team, scheduled_date, points, rebounds,
            assists, and total_score.

        Example:
            Get all game stats for detailed analysis::

                with Database(config) as db:
                    game_stats = db.get_game_stats_export(2026)
                    # Group by game for analysis
                    by_game = {}
                    for stat in game_stats:
                        game_id = stat['game_id']
                        by_game.setdefault(game_id, []).append(stat)
        """
        query = "SELECT * FROM v_game_stats_export WHERE tournament_year = %s"

        with self.conn.cursor() as cur:
            cur.execute(query, (year,))
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

        logger.info(f"Fetched {len(results)} game stat records (year: {year})")
        return results
