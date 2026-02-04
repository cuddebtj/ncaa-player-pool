# Quick Start

Get up and running in 5 minutes.

## 1. Install

```bash
git clone https://github.com/cuddebtj/ncaa-player-pool.git
cd ncaa-player-pool
uv sync
cp .env.example .env
# Edit .env with your database and Google credentials
```

## 2. Initialize Database

```bash
./ncaa-pool init
```

## 3. Setup Tournament (Selection Sunday)

```bash
./setup-tournament.sh 2026
```

This fetches:

- Tournament bracket with seeds
- All team rosters
- Exports to Google Sheets

## 4. Daily Updates (During Tournament)

```bash
./update-tournament.sh 2026
```

Or schedule with cron:

```bash
0 2 * 3-4 * cd /path/to/ncaa-player-pool && ./update-tournament.sh 2026
```

## 5. View Stats

```bash
./ncaa-pool stats --year 2026
```
