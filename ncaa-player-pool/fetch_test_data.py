"""
Test script to fetch sample ESPN API data for schema exploration.
This will download tournament, team, and game data to data/espn/ directory.
"""

import asyncio
from pathlib import Path

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from logger import setup_logger
from api_client import APIClient
from espn_api import ESPNService


async def main():
    """Fetch test data from ESPN API."""

    # Setup
    config = get_config()
    logger = setup_logger(
        name="ncaa_pool",
        level=config.log_level,
        log_file=config.log_file,
    )

    logger.info("=" * 80)
    logger.info("Starting ESPN API test data fetch")
    logger.info("=" * 80)

    async with APIClient(config) as client:
        espn = ESPNService(config, client)

        # 1. Fetch Current Scoreboard
        logger.info("\n[1/4] Fetching current scoreboard...")
        teams = []
        game_ids = []
        team_ids = set()

        try:
            scoreboard_data = await espn.fetch_scoreboard(save=True)
            events = scoreboard_data.get("events", [])
            logger.info(f"✓ Scoreboard saved ({len(events)} games)")

            # Extract game IDs and team IDs from scoreboard
            for event in events:
                event_id = event.get("id")
                if event_id:
                    game_ids.append(event_id)

                competitions = event.get("competitions", [])
                for comp in competitions:
                    for competitor in comp.get("competitors", []):
                        team_id = competitor.get("id")
                        if team_id:
                            team_ids.add(team_id)
                            team_info = {
                                "id": team_id,
                                "name": competitor.get("team", {}).get("displayName"),
                                "abbreviation": competitor.get("team", {}).get("abbreviation"),
                            }
                            teams.append(team_info)

            logger.info(f"✓ Found {len(team_ids)} unique teams")
            logger.info(f"✓ Found {len(game_ids)} games")

        except Exception as e:
            logger.error(f"✗ Failed to fetch scoreboard: {e}")
            logger.info("Cannot continue without scoreboard data")
            return

        # 2. Fetch Sample Team Data (first 3 teams)
        logger.info(f"\n[2/4] Fetching sample team data (first 3 of {len(team_ids)} teams)...")
        try:
            sample_team_ids = list(team_ids)[:3]

            if sample_team_ids:
                for team_id in sample_team_ids:
                    team_data = await espn.fetch_team(team_id, save=True)
                    team_name = team_data.get("team", {}).get("displayName", "Unknown")
                    logger.info(f"✓ Fetched team: {team_name}")
            else:
                logger.warning("No team IDs found in scoreboard data")

        except Exception as e:
            logger.error(f"✗ Failed to fetch teams: {e}")

        # 3. Fetch Sample Game Data (first 3 games)
        logger.info(f"\n[3/4] Fetching sample game data (first 3 of {len(game_ids)} games)...")
        try:
            sample_games = game_ids[:3] if len(game_ids) >= 3 else game_ids

            if sample_games:
                for game_id in sample_games:
                    game_data = await espn.fetch_game_summary(game_id, save=True)
                    logger.info(f"✓ Fetched game: {game_id}")
            else:
                logger.warning("No game IDs found in scoreboard data")

        except Exception as e:
            logger.error(f"✗ Failed to fetch games: {e}")

        # 4. Try Tournament Data (may not exist until March Madness)
        logger.info("\n[4/4] Attempting to fetch tournament bracket...")
        try:
            tournament_data = await espn.fetch_tournament(save=True)
            logger.info(f"✓ Tournament data saved")
        except Exception as e:
            logger.warning(f"Tournament bracket not available (expected if not March): {e}")

    logger.info("\n" + "=" * 80)
    logger.info("Test data fetch complete!")
    logger.info(f"Data saved to: {config.data_dir / 'espn'}")
    logger.info("=" * 80)

    # Print directory structure
    espn_dir = config.data_dir / "espn"
    if espn_dir.exists():
        logger.info("\nFiles created:")
        for subdir in ["tournaments", "teams", "games"]:
            subdir_path = espn_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*.json"))
                logger.info(f"  {subdir}/: {len(files)} files")
                for f in files[:5]:  # Show first 5 files
                    logger.info(f"    - {f.name}")
                if len(files) > 5:
                    logger.info(f"    ... and {len(files) - 5} more")


if __name__ == "__main__":
    asyncio.run(main())
