# API Reference

This section provides detailed API documentation for all modules in the NCAA Player Pool package.

## Package Structure

```text
ncaa_player_pool/
├── __init__.py      # Package exports
├── models.py        # Pydantic data models
├── config.py        # Configuration management
├── logger.py        # Logging utilities
├── api_client.py    # HTTP client with retry logic
├── db.py            # Database operations
├── espn_api.py      # ESPN API integration
├── transformers.py  # Data transformation functions
├── sheets.py        # Google Sheets export
└── __main__.py      # CLI entry point
```

## Modules

### Core Models

- [**models**](models.md) - Pydantic models for ESPN API responses and database entities

### Configuration

- [**config**](config.md) - Application configuration and environment variables

### Data Layer

- [**db**](db.md) - PostgreSQL database operations
- [**espn_api**](espn_api.md) - ESPN API client and data fetching
- [**transformers**](transformers.md) - Transform ESPN data to database models

### Export

- [**sheets**](sheets.md) - Google Sheets integration and export

## Quick Import Examples

```python
# Import models
from ncaa_player_pool.models import Player, Team, PlayerGameStats

# Import configuration
from ncaa_player_pool.config import get_config, Config

# Import database
from ncaa_player_pool.db import Database

# Import ESPN service
from ncaa_player_pool.espn_api import ESPNService
```
