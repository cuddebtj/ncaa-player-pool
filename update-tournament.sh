#!/usr/bin/env bash
# Tournament Update Script
# Fetches latest stats and exports to Google Sheets
# Run this daily during the tournament

set -e  # Exit on error

YEAR="${1:-2026}"
DATE="$2"  # Optional: YYYYMMDD format

cd "$(dirname "$0")"

echo "=========================================="
echo "NCAA Player Pool - Tournament Update"
echo "Year: $YEAR"
if [ -n "$DATE" ]; then
    echo "Date: $DATE"
fi
echo "=========================================="
echo ""

# Update stats
echo "[1/2] Updating player statistics..."
if [ -n "$DATE" ]; then
    ./ncaa-pool update-stats --year "$YEAR" --date "$DATE"
else
    ./ncaa-pool update-stats --year "$YEAR"
fi

echo ""
echo "[2/2] Exporting to Google Sheets..."
./ncaa-pool export --year "$YEAR"

echo ""
echo "=========================================="
echo "✓ Tournament update complete!"
echo "=========================================="
