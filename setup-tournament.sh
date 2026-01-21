#!/usr/bin/env bash
# Tournament Setup Script
# Run this ONCE when the tournament bracket is announced (Selection Sunday)

set -e  # Exit on error

YEAR="${1:-2026}"

cd "$(dirname "$0")"

echo "=========================================="
echo "NCAA Player Pool - Tournament Setup"
echo "Year: $YEAR"
echo "=========================================="
echo ""

# Check if database is initialized
echo "[1/4] Checking database..."
./ncaa-pool stats --year "$YEAR" --limit 1 > /dev/null 2>&1 || {
    echo "Database not initialized. Run: ./ncaa-pool init"
    exit 1
}
echo "✓ Database ready"

echo ""
echo "[2/4] Fetching tournament bracket..."
./ncaa-pool fetch-tournament --year "$YEAR" || {
    echo "⚠ Tournament bracket not available yet (expected before March Madness)"
    echo "   Continuing with current teams from scoreboard..."
}

echo ""
echo "[3/4] Fetching team rosters..."
./ncaa-pool fetch-rosters --year "$YEAR"

echo ""
echo "[4/4] Exporting to Google Sheets..."
./ncaa-pool export --year "$YEAR"

echo ""
echo "=========================================="
echo "✓ Tournament setup complete!"
echo ""
echo "Next steps:"
echo "1. Check your Google Sheet - Players sheet should be populated"
echo "2. Participants can now fill out your Google Form"
echo "3. During tournament, run: ./update-tournament.sh $YEAR"
echo "=========================================="
