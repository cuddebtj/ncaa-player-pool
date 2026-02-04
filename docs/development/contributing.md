# Contributing

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/cuddebtj/ncaa-player-pool.git
cd ncaa-player-pool
uv sync --extra dev
```

## Code Quality

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

### Type Checking

```bash
uv run ty check src/ncaa_player_pool
```

### Testing

```bash
uv run pytest
```

### Pre-commit

Install hooks:

```bash
uv run pre-commit install
```

## Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run all quality checks
5. Submit a pull request

## Documentation

Build docs locally:

```bash
uv run mkdocs serve
```

View at http://localhost:8000
