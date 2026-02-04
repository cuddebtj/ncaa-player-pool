# NCAA Player Pool

A comprehensive application for managing NCAA Tournament player pools with automatic stat tracking and Google Sheets integration.

## Overview

NCAA Player Pool automates the tedious work of running a March Madness player pool:

- **Automatic data collection** from ESPN's API
- **Player statistics tracking** (points, rebounds, assists)
- **Google Sheets integration** for easy sharing with participants
- **CLI interface** for simple operation

## How It Works

```text
ESPN API → Fetch Data → PostgreSQL → Export → Google Sheets → Participants
```

1. **Setup**: Run once when the tournament bracket is announced
2. **Daily Updates**: Run during the tournament to update stats
3. **View Results**: Participants see live stats in Google Sheets

## Game Rules

The default scoring system:

- Each participant selects **16 players** (one from each seed 1-16)
- Players must be from teams with the corresponding tournament seed
- **Scoring**: Points + Rebounds + Assists
- When a team is eliminated, their players stop accumulating points
- Winner has the highest total score at tournament end

## Quick Links

- [Installation Guide](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [CLI Reference](cli.md)
- [API Reference](api/index.md)

## Requirements

- Python 3.11+
- PostgreSQL database
- Google Cloud account (for Sheets export)
- `uv` package manager
