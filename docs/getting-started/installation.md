# Installation

## Prerequisites

- **Python 3.11+**
- **PostgreSQL** database
- **Google Cloud account** (for Sheets export)
- **uv** package manager

## Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Clone Repository

```bash
git clone https://github.com/cuddebtj/ncaa-player-pool.git
cd ncaa-player-pool
```

## Install Dependencies

```bash
uv sync
```

For development with docs:

```bash
uv sync --extra dev
```

## Configure Environment

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` with your settings:

```bash
# Required
POSTGRES_CONN_STR=postgresql://user:password@host:5432/database

# For Google Sheets export
GOOGLE_CREDENTIALS_FILE=/path/to/service-account.json
GOOGLE_SHEET_ID=your_spreadsheet_id
```

## Initialize Database

```bash
./ncaa-pool init
```

## Verify Installation

```bash
./ncaa-pool --help
```
