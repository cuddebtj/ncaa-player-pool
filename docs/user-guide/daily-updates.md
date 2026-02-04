# Daily Updates

Keep your pool statistics current during the tournament.

## Update Command

```bash
./update-tournament.sh 2026
```

Or manually:

```bash
./ncaa-pool update-stats --year 2026
./ncaa-pool export --year 2026
```

## Scheduling Updates

### Using Cron

```bash
crontab -e
```

Add:

```bash
# Run at 2 AM daily during March-April
0 2 * 3-4 * cd /path/to/ncaa-player-pool && ./update-tournament.sh 2026 >> /var/log/ncaa-pool.log 2>&1
```

### Recommended Schedule

- **During games**: Every few hours
- **After games end**: Once daily (2-3 AM)

## Specific Dates

Update stats for a specific game date:

```bash
./ncaa-pool update-stats --year 2026 --date 20260319
```

## Troubleshooting

### No New Stats

1. Check if games have finished
2. View logs: `tail -f logs/ncaa_pool.log`
3. Verify database connection

### API Errors

ESPN API may be temporarily unavailable during high traffic.
The app automatically retries with exponential backoff.
