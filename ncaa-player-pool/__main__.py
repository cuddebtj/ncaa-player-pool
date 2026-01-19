"""
NCAA Player Pool CLI Application
Main entry point with Typer commands.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, Config
from logger import setup_logger, get_logger
from api_client import APIClient
from espn_api import ESPNService
from db import Database
from transformers import (
    transform_roster_to_players,
    transform_scoreboard_to_games,
    transform_scoreboard_to_teams,
    transform_game_summary_to_player_stats,
    transform_game_summary_to_game,
    transform_tournament_to_tournament,
    transform_tournament_to_teams,
)
from models import ESPNScoreboard, ESPNGameSummary, ESPNRosterResponse, ESPNTournament

# Initialize Typer app
app = typer.Typer(
    name="ncaa-pool",
    help="NCAA Tournament Player Pool - Manage tournament data and player statistics",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


def get_app_config() -> Config:
    """Get application configuration and set up logging."""
    config = get_config()
    setup_logger(
        name="ncaa_pool",
        level=config.log_level,
        log_file=config.log_file,
    )
    return config


@app.command()
def init(
    migration_file: Optional[Path] = typer.Option(
        None,
        "--migration",
        "-m",
        help="Path to migration file (default: migrations/001_initial_schema.sql)",
    ),
):
    """
    Initialize the database schema.
    Runs the SQL migration to create tables, views, and functions.
    """
    config = get_app_config()
    logger = get_logger(__name__)

    if migration_file is None:
        migration_file = Path("migrations/001_initial_schema.sql")

    if not migration_file.exists():
        console.print(f"[red]Error: Migration file not found: {migration_file}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Initializing database...[/cyan]")
    console.print(f"Migration file: {migration_file}")

    try:
        with Database(config) as db:
            db.run_migration(migration_file)

        console.print("[green]✓ Database initialized successfully![/green]")

    except Exception as e:
        logger.exception(f"Database initialization failed: {e}")
        console.print(f"[red]✗ Database initialization failed: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def fetch_rosters(
    year: int = typer.Option(..., "--year", "-y", help="Tournament year"),
    team_ids: Optional[str] = typer.Option(
        None,
        "--teams",
        "-t",
        help="Comma-separated team IDs (if not provided, fetches from scoreboard)",
    ),
    save_responses: bool = typer.Option(
        True, "--save/--no-save", help="Save API responses to files"
    ),
):
    """
    Fetch team rosters and store in database.

    If team IDs are not provided, fetches current teams from scoreboard.
    """
    config = get_app_config()
    logger = get_logger(__name__)

    console.print(f"[cyan]Fetching rosters for year {year}...[/cyan]")

    async def fetch():
        async with APIClient(config) as client:
            espn = ESPNService(config, client)

            # Get team IDs
            if team_ids:
                team_id_list = [tid.strip() for tid in team_ids.split(",")]
                console.print(f"Using provided team IDs: {len(team_id_list)} teams")
            else:
                console.print("Fetching team IDs from scoreboard...")
                scoreboard_data = await espn.fetch_scoreboard(save=save_responses)
                scoreboard = ESPNScoreboard.model_validate(scoreboard_data)

                # Extract unique team IDs
                team_id_set = set()
                for event in scoreboard.events:
                    for comp in event.competitions:
                        for competitor in comp.competitors:
                            team_id_set.add(competitor.id)

                team_id_list = list(team_id_set)
                console.print(f"Found {len(team_id_list)} teams from scoreboard")

            # Fetch rosters
            console.print(f"Fetching rosters for {len(team_id_list)} teams...")
            roster_responses = await espn.fetch_rosters_batch(team_id_list, save=save_responses)

            # Transform and save to database
            with Database(config) as db:
                total_players = 0

                for roster_data in roster_responses:
                    try:
                        roster = ESPNRosterResponse.model_validate(roster_data)
                        team, players = transform_roster_to_players(roster, year)

                        # Save to database
                        db.upsert_team(team)
                        for player in players:
                            db.upsert_player(player)

                        total_players += len(players)
                        console.print(f"  ✓ {team.name}: {len(players)} players")

                    except Exception as e:
                        logger.error(f"Failed to process roster: {e}")
                        console.print(f"  [yellow]✗ Failed to process roster: {e}[/yellow]")

            console.print(f"[green]✓ Saved {len(roster_responses)} teams and {total_players} players[/green]")

    try:
        asyncio.run(fetch())
    except Exception as e:
        logger.exception(f"Roster fetch failed: {e}")
        console.print(f"[red]✗ Roster fetch failed: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def fetch_games(
    year: int = typer.Option(..., "--year", "-y", help="Tournament year"),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Specific date (YYYYMMDD format, e.g., 20260319)",
    ),
    save_responses: bool = typer.Option(
        True, "--save/--no-save", help="Save API responses to files"
    ),
):
    """
    Fetch games from scoreboard and store in database.

    If date is provided, fetches games for that specific date.
    Otherwise, fetches current/recent games.
    """
    config = get_app_config()
    logger = get_logger(__name__)

    console.print(f"[cyan]Fetching games for year {year}...[/cyan]")
    if date:
        console.print(f"Date filter: {date}")

    async def fetch():
        async with APIClient(config) as client:
            espn = ESPNService(config, client)

            # Fetch scoreboard
            scoreboard_data = await espn.fetch_scoreboard(dates=date, save=save_responses)
            scoreboard = ESPNScoreboard.model_validate(scoreboard_data)

            console.print(f"Found {len(scoreboard.events)} games")

            # Transform games and teams
            games = transform_scoreboard_to_games(scoreboard, year)
            teams = transform_scoreboard_to_teams(scoreboard, year)

            # Save to database
            with Database(config) as db:
                # Save teams first
                for team in teams:
                    db.upsert_team(team)

                # Save games
                for game in games:
                    db.upsert_game(game)

            console.print(f"[green]✓ Saved {len(teams)} teams and {len(games)} games[/green]")

    try:
        asyncio.run(fetch())
    except Exception as e:
        logger.exception(f"Game fetch failed: {e}")
        console.print(f"[red]✗ Game fetch failed: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def update_stats(
    year: int = typer.Option(..., "--year", "-y", help="Tournament year"),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Specific date (YYYYMMDD format, e.g., 20260319)",
    ),
    save_responses: bool = typer.Option(
        True, "--save/--no-save", help="Save API responses to files"
    ),
):
    """
    Update player statistics from game summaries.

    Fetches detailed game summaries with player box scores and updates the database.
    """
    config = get_app_config()
    logger = get_logger(__name__)

    console.print(f"[cyan]Updating player statistics for year {year}...[/cyan]")

    async def update():
        async with APIClient(config) as client:
            espn = ESPNService(config, client)

            # Get games from scoreboard
            scoreboard_data = await espn.fetch_scoreboard(dates=date, save=False)
            scoreboard = ESPNScoreboard.model_validate(scoreboard_data)

            game_ids = [event.id for event in scoreboard.events]
            console.print(f"Found {len(game_ids)} games to update")

            # Fetch game summaries
            console.print("Fetching game summaries...")
            game_summaries = await espn.fetch_games_batch(game_ids, save=save_responses)

            total_players = 0
            total_stats = 0

            with Database(config) as db:
                for game_data in game_summaries:
                    try:
                        game_summary = ESPNGameSummary.model_validate(game_data)

                        # Transform game
                        game = transform_game_summary_to_game(game_summary, year)
                        db.upsert_game(game)

                        # Transform player stats
                        players, stats_list = transform_game_summary_to_player_stats(game_summary, year)

                        # Save players
                        for player in players:
                            db.upsert_player(player)

                        # Save stats
                        for stats in stats_list:
                            db.upsert_player_game_stats(stats)

                        total_players += len(players)
                        total_stats += len(stats_list)

                        console.print(f"  ✓ Game {game.id}: {len(stats_list)} stat records")

                    except Exception as e:
                        logger.error(f"Failed to process game summary: {e}")
                        console.print(f"  [yellow]✗ Failed to process game: {e}[/yellow]")

            console.print(f"[green]✓ Updated {total_players} players with {total_stats} stat records[/green]")

    try:
        asyncio.run(update())
    except Exception as e:
        logger.exception(f"Stats update failed: {e}")
        console.print(f"[red]✗ Stats update failed: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def fetch_tournament(
    year: int = typer.Option(..., "--year", "-y", help="Tournament year"),
    tournament_id: Optional[str] = typer.Option(
        None,
        "--id",
        "-i",
        help="Tournament ID (default: NCAA Men's tournament)",
    ),
    save_responses: bool = typer.Option(
        True, "--save/--no-save", help="Save API responses to files"
    ),
):
    """
    Fetch tournament bracket with seeds.

    Only available during March Madness tournament period.
    Updates team seeds in the database.
    """
    config = get_app_config()
    logger = get_logger(__name__)

    console.print(f"[cyan]Fetching tournament bracket for year {year}...[/cyan]")

    async def fetch():
        async with APIClient(config) as client:
            espn = ESPNService(config, client)

            # Fetch tournament
            tournament_data = await espn.fetch_tournament(
                tournament_id=tournament_id,
                save=save_responses
            )
            tournament_espn = ESPNTournament.model_validate(tournament_data)

            # Transform
            tournament = transform_tournament_to_tournament(tournament_espn)
            teams = transform_tournament_to_teams(tournament_espn, year)

            # Save to database
            with Database(config) as db:
                db.upsert_tournament(tournament)

                for team in teams:
                    db.upsert_team(team)

            console.print(f"[green]✓ Saved tournament with {len(teams)} seeded teams[/green]")

    try:
        asyncio.run(fetch())
    except Exception as e:
        logger.exception(f"Tournament fetch failed: {e}")
        console.print(f"[red]✗ Tournament fetch failed: {e}[/red]")
        console.print("[yellow]Note: Tournament bracket may not be available until March Madness starts[/yellow]")
        raise typer.Exit(code=1)


@app.command()
def stats(
    year: int = typer.Option(..., "--year", "-y", help="Tournament year"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of top players to show"),
):
    """
    Show top player statistics from the database.
    """
    config = get_app_config()
    logger = get_logger(__name__)

    try:
        with Database(config) as db:
            data = db.get_player_stats_export(year)

        if not data:
            console.print(f"[yellow]No statistics found for year {year}[/yellow]")
            return

        # Create rich table
        table = Table(title=f"Top {limit} Players - {year}")
        table.add_column("Player", style="cyan")
        table.add_column("Team", style="magenta")
        table.add_column("Seed", justify="center")
        table.add_column("Games", justify="right")
        table.add_column("PTS", justify="right", style="green")
        table.add_column("REB", justify="right", style="blue")
        table.add_column("AST", justify="right", style="yellow")
        table.add_column("Total", justify="right", style="bold green")

        for row in data[:limit]:
            table.add_row(
                row["player_name"],
                row["team_name"],
                str(row["seed"]) if row["seed"] else "-",
                str(row["games_played"]),
                str(row["total_points"]),
                str(row["total_rebounds"]),
                str(row["total_assists"]),
                str(row["total_score"]),
            )

        console.print(table)

    except Exception as e:
        logger.exception(f"Stats display failed: {e}")
        console.print(f"[red]✗ Failed to retrieve stats: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
