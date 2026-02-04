# CLI Reference

The NCAA Player Pool CLI provides commands for managing tournament data.

## Usage

```bash
./ncaa-pool [COMMAND] [OPTIONS]
```

Or using `uv`:

```bash
uv run ncaa-pool [COMMAND] [OPTIONS]
```

## Commands

### init

Initialize the database schema.

```bash
./ncaa-pool init [--migration FILE]
```

**Options:**

- `--migration`, `-m`: Path to migration file (default: `migrations/001_initial_schema.sql`)

### fetch-tournament

Fetch tournament bracket with team seeds.

```bash
./ncaa-pool fetch-tournament --year YEAR
```

**Options:**

- `--year`, `-y`: Tournament year (required)

!!! note
    Tournament bracket is only available after Selection Sunday.

### fetch-rosters

Fetch team rosters and store in database.

```bash
./ncaa-pool fetch-rosters --year YEAR
```

**Options:**

- `--year`, `-y`: Tournament year (required)

### fetch-games

Fetch games from scoreboard.

```bash
./ncaa-pool fetch-games --year YEAR [--date DATE]
```

**Options:**

- `--year`, `-y`: Tournament year (required)
- `--date`, `-d`: Specific date in YYYYMMDD format (optional)

### update-stats

Update player statistics from game summaries.

```bash
./ncaa-pool update-stats --year YEAR [--date DATE]
```

**Options:**

- `--year`, `-y`: Tournament year (required)
- `--date`, `-d`: Specific date in YYYYMMDD format (optional)

### stats

Display top player statistics.

```bash
./ncaa-pool stats --year YEAR [--limit N]
```

**Options:**

- `--year`, `-y`: Tournament year (required)
- `--limit`, `-l`: Number of players to show (default: 20)

### export

Export data to Google Sheets.

```bash
./ncaa-pool export --year YEAR [--sheet-id ID]
```

**Options:**

- `--year`, `-y`: Tournament year (required)
- `--sheet-id`, `-s`: Google Sheets ID (optional, uses env var if not specified)

## Examples

### Tournament Setup

```bash
# Initialize database (run once)
./ncaa-pool init

# Fetch bracket and rosters (after Selection Sunday)
./ncaa-pool fetch-tournament --year 2026
./ncaa-pool fetch-rosters --year 2026
./ncaa-pool export --year 2026
```

### Daily Updates

```bash
# Update stats and export
./ncaa-pool update-stats --year 2026
./ncaa-pool export --year 2026
```

### View Stats

```bash
# Show top 20 players
./ncaa-pool stats --year 2026

# Show top 50 players
./ncaa-pool stats --year 2026 --limit 50
```
