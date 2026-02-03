"""
Database connection and operations module.
Handles PostgreSQL connections and common database operations.
"""

from pathlib import Path
from typing import Any

import psycopg
from config import Config
from logger import get_logger
from models import (
    Game,
    Player,
    PlayerGameStats,
    Team,
    Tournament,
)
from psycopg import sql

logger = get_logger(__name__)


class Database:
    """Database connection and operations manager."""

    def __init__(self, config: Config):
        """
        Initialize database manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.conn: psycopg.Connection | None = None

    def connect(self) -> psycopg.Connection:
        """
        Connect to PostgreSQL database.

        Returns:
            Database connection

        Raises:
            psycopg.DatabaseError: If connection fails
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

    def close(self):
        """Close database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            logger.error(f"Database transaction error: {exc_val}")
            if self.conn:
                self.conn.rollback()
        else:
            if self.conn:
                self.conn.commit()
        self.close()

    def run_migration(self, migration_file: Path):
        """
        Run a SQL migration file.

        Args:
            migration_file: Path to SQL migration file

        Raises:
            FileNotFoundError: If migration file doesn't exist
            psycopg.DatabaseError: If migration fails
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
        """
        Insert or update tournament record.

        Args:
            tournament: Tournament model instance
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
        """
        Insert or update team record.

        Args:
            team: Team model instance
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
        """
        Insert or update player record.

        Args:
            player: Player model instance
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
        """
        Insert or update game record.

        Args:
            game: Game model instance
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
        """
        Insert or update player game statistics.

        Args:
            stats: PlayerGameStats model instance
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
        """
        Get player data for Google Sheets export.

        Args:
            year: Tournament year

        Returns:
            List of player export dictionaries
        """
        query = "SELECT * FROM v_players_export WHERE tournament_year = %s"

        with self.conn.cursor() as cur:
            cur.execute(query, (year,))
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

        logger.info(f"Fetched {len(results)} players for export (year: {year})")
        return results

    def get_player_stats_export(self, year: int) -> list[dict[str, Any]]:
        """
        Get player statistics for Google Sheets export.

        Args:
            year: Tournament year

        Returns:
            List of player stats export dictionaries
        """
        query = "SELECT * FROM v_player_stats_export WHERE tournament_year = %s"

        with self.conn.cursor() as cur:
            cur.execute(query, (year,))
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

        logger.info(f"Fetched stats for {len(results)} players (year: {year})")
        return results

    def get_game_stats_export(self, year: int) -> list[dict[str, Any]]:
        """
        Get game-by-game statistics for Google Sheets export.

        Args:
            year: Tournament year

        Returns:
            List of game stats export dictionaries
        """
        query = "SELECT * FROM v_game_stats_export WHERE tournament_year = %s"

        with self.conn.cursor() as cur:
            cur.execute(query, (year,))
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

        logger.info(f"Fetched {len(results)} game stat records (year: {year})")
        return results
