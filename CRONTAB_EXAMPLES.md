# Crontab Examples for NCAA Player Pool Updates

This document contains example cron jobs for automating tournament data updates.

## Cron Format Reminder

```
* * * * * command to execute
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

## Option 1: Daily Post-Game Updates (Recommended)

Run once per day at 2:00 AM (after all games have finished) during March and April:

```bash
0 2 * 3-4 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

**Pros:**
- Simple, reliable
- Stats are always final (no in-progress games)
- Minimal API requests

**Cons:**
- Leaderboard only updates once per day
- No live updates during games

## Option 2: Live Updates During Game Times

Run every 15 minutes during typical game times (2:00 PM - 11:00 PM) in March and April:

```bash
*/15 14-23 * 3-4 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

Run every 30 minutes during game times:

```bash
*/30 14-23 * 3-4 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

**Pros:**
- Near real-time leaderboard updates
- See standings change as games progress
- More engaging for participants

**Cons:**
- More API requests
- Shows in-progress stats until games finish
- May take several minutes per update cycle

## Option 3: Multiple Updates Per Day

Run at specific times when games typically start (12:00 PM, 4:00 PM, 7:00 PM, 10:00 PM):

```bash
0 12,16,19,22 * 3-4 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

**Pros:**
- Catches multiple game windows
- Less frequent than live updates
- Balances freshness with API usage

**Cons:**
- Still might show in-progress stats
- May miss late-night games

## Option 4: Tournament-Specific Schedule

### First Four / First Round (frequent updates)
```bash
# Every 30 minutes during game days
*/30 12-23 16-19 3 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

### Sweet Sixteen / Elite Eight (moderate updates)
```bash
# Every hour during game days
0 12-23 26-29 3 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

### Final Four / Championship (frequent updates)
```bash
# Every 15 minutes during game days
*/15 12-23 5-7 4 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

### Post-tournament (daily cleanup)
```bash
# Once daily after tournament ends
0 2 * 4-5 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

## Setup Instructions

1. **Edit your crontab:**
   ```bash
   crontab -e
   ```

2. **Add one or more of the examples above**

3. **Update the year** (change `2026` to current tournament year)

4. **Update the path** if your project is in a different location

5. **Save and exit** (usually `:wq` in vim or `Ctrl+X` in nano)

6. **Verify crontab is set:**
   ```bash
   crontab -l
   ```

## Testing Cron Jobs

Before setting up cron, test the script manually:

```bash
cd /home/dev/projects/ncaa-player-pool
./update-tournament.sh 2026
```

## Monitoring Cron Jobs

View cron execution logs:

```bash
# On most systems:
grep CRON /var/log/syslog

# Or check application logs:
tail -f logs/ncaa_pool.log
```

## Troubleshooting

### Cron Job Not Running

1. **Check cron service is running:**
   ```bash
   sudo service cron status
   ```

2. **Verify environment variables:**
   - Cron runs with minimal environment
   - The wrapper script (`ncaa-pool`) loads `.env` automatically
   - Ensure `.env` file exists in project directory

3. **Check permissions:**
   ```bash
   chmod +x update-tournament.sh
   chmod +x ncaa-pool
   ```

4. **Use absolute paths:**
   - Always use full path to project directory
   - Example: `/home/dev/projects/ncaa-player-pool/update-tournament.sh`

### High API Usage

If you're hitting rate limits or getting errors:

1. **Reduce frequency** - Switch from */15 to */30 or hourly
2. **Narrow time window** - Only run during actual game times
3. **Check ESPN API rate limits** - The app has 2.5s delays built in

## Recommended Setup

For most users, start with **Option 1** (daily updates):

```bash
0 2 * 3-4 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

If you want live updates during the tournament, upgrade to **Option 2** (every 30 minutes):

```bash
*/30 14-23 * 3-4 * cd /home/dev/projects/ncaa-player-pool && ./update-tournament.sh 2026
```

## Notes

- All times are in **your server's local timezone**
- The application handles duplicates safely via upsert operations
- Google Sheets export replaces all data, so frequency = how fresh your leaderboard is
- March Madness typically runs mid-March through early April (dates vary yearly)
