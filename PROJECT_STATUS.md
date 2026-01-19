# NCAA Player Pool - Project Status

**Last Updated:** 2026-01-19
**Status:** Core functionality complete, ready for Google Sheets integration

## 📋 Project Overview

NCAA Tournament Player Pool game where participants select 16 players (one from each seed 1-16) and compete based on players' tournament performance. Scoring: Points + Rebounds + Assists.

## ✅ Completed Components

### 1. Infrastructure ✓
- **Configuration Management** ([config.py](ncaa-player-pool/config.py))
  - Environment-based configuration with `.env` support
  - Database connection, API settings, logging config
  - **Note:** Password in `.env` must be URL-encoded (use `%2F` for `/`, `%3D` for `=`)

- **Logging** ([logger.py](ncaa-player-pool/logger.py))
  - File rotation (10MB max, 5 backups)
  - Console + file output
  - Logs stored in `logs/ncaa_pool.log`

- **API Client** ([api_client.py](ncaa-player-pool/api_client.py))
  - httpx-based async HTTP client
  - Automatic retries with exponential backoff (tenacity)
  - Rate limiting (2.5s between requests)
  - Response caching to JSON files
  - Error handling for 404, 429, 5xx errors

### 2. ESPN API Integration ✓
- **Service Layer** ([espn_api.py](ncaa-player-pool/espn_api.py))
  - Scoreboard fetching (current/recent games)
  - **Team roster fetching** (discovered endpoint: `/teams/{id}/roster`)
  - Game summary with box scores
  - Tournament bracket (March Madness only)
  - Batch operations for efficiency

- **API Documentation** ([ESPN_API_SCHEMA.md](ESPN_API_SCHEMA.md))
  - Complete documentation of undocumented ESPN API
  - Endpoints, response structures, examples
  - **Key Discovery:** Roster endpoint exists! No need to build roster from game data

### 3. Data Models ✓
- **Pydantic Models** ([models.py](ncaa-player-pool/models.py))
  - ESPN API response models (scoreboard, games, teams, rosters, tournament)
  - Database entity models (tournaments, teams, players, games, stats)
  - Export models for Google Sheets

### 4. Database ✓
- **Schema** ([migrations/001_initial_schema.sql](migrations/001_initial_schema.sql))
  - PostgreSQL with `ncaa_pool` schema
  - Tables: tournaments, teams, players, games, player_game_stats
  - Composite primary keys (id, year) for multi-year support
  - Views for Google Sheets export: `v_players_export`, `v_player_stats_export`, `v_game_stats_export`
  - Helper functions for queries

- **Operations** ([db.py](ncaa-player-pool/db.py))
  - Connection management with context manager
  - Upsert methods for all entities (handles duplicates)
  - Export data retrieval methods
  - Migration runner

### 5. Data Transformation ✓
- **Transformers** ([transformers.py](ncaa-player-pool/transformers.py))
  - Roster → Team + Players
  - Scoreboard → Games + Teams
  - Game Summary → Game + Players + Stats
  - Tournament → Tournament + Teams (with seeds)
  - **Important Fix:** Handles both ESPN stat formats (uppercase abbreviations & lowercase names)

### 6. CLI Application ✓
- **Typer CLI** ([__main__.py](ncaa-player-pool/__main__.py))
  - Beautiful Rich-based output with tables
  - Commands implemented:
    - `./ncaa-pool init` - Initialize database
    - `./ncaa-pool fetch-rosters --year 2026` - Fetch team rosters
    - `./ncaa-pool fetch-games --year 2026 [--date YYYYMMDD]` - Fetch games
    - `./ncaa-pool update-stats --year 2026 [--date YYYYMMDD]` - Update player stats
    - `./ncaa-pool fetch-tournament --year 2026` - Fetch tournament bracket (March only)
    - `./ncaa-pool stats --year 2026 [--limit 20]` - Display top players

- **Wrapper Script** ([ncaa-pool](ncaa-pool))
  - Handles environment variable loading
  - Unsets cached vars to force `.env` reload
  - Usage: `./ncaa-pool <command> [options]`

## 🧪 Tested & Working

### Test Results (2026-01-19)
- ✅ Database initialization successful
- ✅ Fetched 2 teams (Houston Cougars, Arizona State Sun Devils)
- ✅ Loaded 30 players into database
- ✅ Fetched game summary for game 401827631
- ✅ Parsed and stored 30 player stat records
- ✅ Stats display working with correct totals

### Current Data in Database
```
Tournament Year: 2026
Teams: 2 (Houston, Arizona State)
Players: 30
Games: 1
Player Stats: 30 records

Top Player: Kingston Flemings (Houston) - 32 points (20 PTS + 4 REB + 8 AST)
```

## 🚧 Pending Work

### 1. Google Sheets Integration (Next Priority)
**Files to create:**
- `ncaa-player-pool/sheets.py` - Google Sheets client
- Add gspread/google-auth integration

**Tasks:**
- [ ] Set up Google Sheets API authentication
- [ ] Create export functions for:
  - Player roster (for entry selection)
  - Player stats (leaderboard)
  - Entry management (manual in sheets)
- [ ] Add CLI command: `./ncaa-pool export --year 2026`
- [ ] Format sheets with formulas for totals/rankings

**Google Sheets Structure:**
1. **Players Sheet** - All available players with teams/seeds
2. **Stats Sheet** - Updated player statistics
3. **Entries Sheet** - Manual entry management (16 players per entry)
4. **Leaderboard Sheet** - Calculated rankings with formulas

### 2. Documentation
- [ ] Update README.md with:
  - Installation instructions
  - Configuration setup (especially URL encoding passwords!)
  - Usage examples for all commands
  - Google Sheets setup guide
  - Workflow for tournament (fetch rosters → entries → update stats → export)

### 3. Nice-to-Have Enhancements
- [ ] Schedule support (cron jobs for auto-updates during tournament)
- [ ] Email/webhook notifications when stats update
- [ ] Historical data comparison (year-over-year)
- [ ] CLI command to validate entries (ensure 1 player per seed)

## 📝 Important Notes

### Environment Variables
**Critical:** Passwords with special characters MUST be URL-encoded in `.env`:
```bash
# Wrong (will fail):
POSTGRES_CONN_STR=postgresql://user:pass/word@host:5432/db

# Right:
POSTGRES_CONN_STR=postgresql://user:pass%2Fword@host:5432/db
```

Common encodings:
- `/` → `%2F`
- `=` → `%3D`
- `@` → `%40`
- `:` → `%3A`

Use: `python -c "from urllib.parse import quote; print(quote('your/password', safe=''))"`

### ESPN API Stat Formats
The transformer handles both formats:
- **Format 1:** Uppercase abbreviations (`PTS`, `REB`, `AST`)
- **Format 2:** Lowercase names (`points`, `rebounds`, `assists`)

Both work correctly after the fix in transformers.py:299-309

### Running Commands
Always use the wrapper script `./ncaa-pool` which handles environment loading:
```bash
./ncaa-pool init
./ncaa-pool fetch-rosters --year 2026
./ncaa-pool update-stats --year 2026
./ncaa-pool stats --year 2026 --limit 10
```

## 🗂️ Project Structure

```
ncaa-player-pool/
├── ncaa-player-pool/           # Main application code
│   ├── __main__.py            # CLI entry point (Typer)
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging setup
│   ├── api_client.py          # HTTP client (httpx + tenacity)
│   ├── espn_api.py            # ESPN API service
│   ├── db.py                  # Database operations
│   ├── models.py              # Pydantic models
│   ├── transformers.py        # Data transformations
│   └── modules/               # Old modules (to be removed)
├── migrations/                # SQL migrations
│   └── 001_initial_schema.sql
├── data/                      # Cached API responses
│   └── espn/
│       ├── tournaments/
│       ├── teams/
│       └── games/
├── logs/                      # Application logs
│   └── ncaa_pool.log
├── ncaa-pool                  # Wrapper script
├── .env                       # Environment variables (gitignored)
├── .env.example              # Example configuration
├── pyproject.toml            # Dependencies
├── ESPN_API_SCHEMA.md        # API documentation
├── PROJECT_STATUS.md         # This file
└── README.md                 # User documentation (needs update)
```

## 🔧 Dependencies

```toml
httpx >= 0.28.1           # Async HTTP client
polars >= 1.25.2          # Data processing (not currently used)
psycopg[binary] >= 3.2.6  # PostgreSQL driver
python-dotenv >= 1.0.1    # Environment variables
pytz >= 2025.1            # Timezone handling
pyyaml >= 6.0.2           # YAML support
typer >= 0.12.0           # CLI framework
tenacity >= 9.0.0         # Retry logic
pydantic >= 2.10.0        # Data validation
gspread >= 6.1.0          # Google Sheets (pending)
google-auth >= 2.37.0     # Google auth (pending)
rich >= 13.7.0            # CLI formatting
```

## 🎯 Quick Start for Next Session

```bash
# 1. Navigate to project
cd /home/dev/projects/ncaa-player-pool

# 2. Check database connection
./ncaa-pool stats --year 2026 --limit 5

# 3. Continue with Google Sheets integration
# Create ncaa-player-pool/sheets.py
# Add export command to __main__.py
# Test export workflow
```

## 💡 Design Decisions

1. **Minimal Database** - Only tournament data, not pool entries (managed in Google Sheets)
2. **Year-Based Partitioning** - All tables include `year` for multi-tournament support
3. **Roster Endpoint** - Teams don't need games to get players (perfect for pre-tournament setup)
4. **Type Safety** - Pydantic models throughout for validation and IDE support
5. **Resilient HTTP** - Automatic retries, rate limiting, comprehensive error handling
6. **Upserts** - All database operations handle duplicates gracefully
7. **Wrapper Script** - Ensures clean environment loading (avoids cached env vars)

## 📞 Contact / Support

For issues or questions, the project was built by Claude (Anthropic) with comprehensive logging and error handling. Check `logs/ncaa_pool.log` for debugging.

---

**Ready to continue!** The foundation is solid and tested. Next step: Google Sheets integration for the dashboard.
