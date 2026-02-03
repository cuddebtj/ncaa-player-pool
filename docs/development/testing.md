# Testing

## Running Tests

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=src/ncaa_player_pool --cov-report=html
```

## Test Structure

```text
tests/
├── conftest.py       # Shared fixtures
├── test_models.py    # Model tests
└── ...
```

## Writing Tests

### Example Test

```python
from ncaa_player_pool.models import ESPNTeamBasic

def test_team_basic():
    team = ESPNTeamBasic(
        id="150",
        displayName="Duke Blue Devils",
        abbreviation="DUKE"
    )
    assert team.id == "150"
    assert team.displayName == "Duke Blue Devils"
```

### Using Fixtures

```python
def test_with_fixture(sample_team):
    team = ESPNTeamBasic(**sample_team)
    assert team.id == "99"
```

## Markers

```bash
# Skip slow tests
uv run pytest -m "not slow"

# Run only integration tests
uv run pytest -m integration
```
