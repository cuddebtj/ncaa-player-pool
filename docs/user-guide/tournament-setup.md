# Tournament Setup

How to set up your player pool for the NCAA Tournament.

## Timeline

1. **Selection Sunday** (mid-March): Bracket announced
2. **Setup Window**: 1-2 days before First Four
3. **Tournament**: ~3 weeks of games

## Setup Steps

### 1. Run Setup Script

After the bracket is announced:

```bash
./setup-tournament.sh 2026
```

This command:

1. Fetches tournament bracket with seeds
2. Fetches all 68 team rosters
3. Exports player list to Google Sheets

### 2. Create Google Form

Create a Google Form for participant entries:

- Entry name
- Participant name/email
- 16 player selections (one per seed)

Link selections to your Player sheet for validation.

### 3. Collect Entries

Share the form with participants before the tournament starts.

### 4. Lock Entries

Before tip-off of the first game, close the form and finalize entries.

## Manual Setup

If you need more control:

```bash
# Fetch bracket
./ncaa-pool fetch-tournament --year 2026

# Fetch rosters
./ncaa-pool fetch-rosters --year 2026

# Export to sheets
./ncaa-pool export --year 2026
```
