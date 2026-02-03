# Configuration

All configuration is managed through environment variables.

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `POSTGRES_CONN_STR` | PostgreSQL connection string |

### Google Sheets

| Variable | Description |
|----------|-------------|
| `GOOGLE_CREDENTIALS_FILE` | Path to service account JSON |
| `GOOGLE_SHEET_ID` | Target spreadsheet ID |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_SCHEMA` | `ncaa_pool` | Database schema name |
| `TOURNAMENT_YEAR` | `2026` | Default tournament year |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `logs/ncaa_pool.log` | Log file path |
| `REQUEST_TIMEOUT` | `30` | HTTP timeout (seconds) |
| `RATE_LIMIT_DELAY` | `2.5` | Delay between API calls |

## Example .env

```bash
# Database
POSTGRES_CONN_STR=postgresql://user:password@localhost:5432/ncaa

# Google Sheets
GOOGLE_CREDENTIALS_FILE=/home/user/credentials.json
GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms

# Optional
DATABASE_SCHEMA=ncaa_pool
TOURNAMENT_YEAR=2026
LOG_LEVEL=INFO
```

## Password Encoding

Special characters in passwords must be URL-encoded:

```bash
# Wrong
POSTGRES_CONN_STR=postgresql://user:pass/word@host/db

# Correct
POSTGRES_CONN_STR=postgresql://user:pass%2Fword@host/db
```

Encode with Python:

```bash
python -c "from urllib.parse import quote; print(quote('your/password', safe=''))"
```
