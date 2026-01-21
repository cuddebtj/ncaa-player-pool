# Google Sheets Integration Setup

This guide explains how to set up Google Sheets integration for exporting NCAA Player Pool data.

## Overview

The application exports two sheets:
1. **Players** - Tournament roster with player info and team seeds
2. **Player Stats** - Game-by-game statistics for all players

Your Google Form populates the **Entries** sheet separately.

## Prerequisites

- A Google Cloud Project (free)
- A Google Sheet for your pool
- 10 minutes

## Step 1: Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the Google Sheets API:
   - Go to **APIs & Services** → **Library**
   - Search for "Google Sheets API"
   - Click **Enable**
4. Create a Service Account:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **Service Account**
   - Name it: `ncaa-pool-export`
   - Click **Create and Continue**
   - Skip role assignment (click **Continue**, then **Done**)

## Step 2: Download Credentials

1. In **Credentials**, click on your service account email
2. Go to **Keys** tab
3. Click **Add Key** → **Create New Key**
4. Choose **JSON** format
5. Click **Create** - the JSON file will download
6. Save it securely (e.g., `~/credentials/ncaa-pool-service-account.json`)

## Step 3: Create Your Google Sheet

1. Create a new Google Sheet or use existing one
2. Name it something like "NCAA Player Pool 2026"
3. Create these sheets manually:
   - **Players** (will be populated by export)
   - **Player Stats** (will be populated by export)
   - **Entries** (populated by your Google Form)
   - Any other sheets you want (leaderboard, etc.)

## Step 4: Share Sheet with Service Account

1. Open the service account JSON file you downloaded
2. Find the `client_email` field (looks like: `ncaa-pool-export@project-name.iam.gserviceaccount.com`)
3. In your Google Sheet, click **Share**
4. Paste the service account email
5. Give it **Editor** permissions
6. Uncheck "Notify people"
7. Click **Share**

## Step 5: Get Sheet ID

From your Google Sheet URL:
```
https://docs.google.com/spreadsheets/d/1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2/edit
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      This is your SHEET_ID
```

Copy the long string between `/d/` and `/edit`

## Step 6: Configure .env File

Add these two lines to your `.env` file:

```bash
GOOGLE_CREDENTIALS_FILE=/path/to/your/service-account.json
GOOGLE_SHEET_ID=1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2
```

**Example:**
```bash
GOOGLE_CREDENTIALS_FILE=/home/dev/credentials/ncaa-pool-service-account.json
GOOGLE_SHEET_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789ABCDEF
```

## Step 7: Test the Export

Run the export command:

```bash
./ncaa-pool export --year 2026
```

You should see:
```
✓ Successfully exported data to Google Sheets!
Spreadsheet URL: https://docs.google.com/spreadsheets/d/...
```

Check your Google Sheet - the **Players** and **Player Stats** sheets should now be populated!

## What Gets Exported

### Players Sheet
Columns:
- Player ID
- Player Name
- Position
- Team
- Team Seed

This is your reference sheet for creating entries. Use it to ensure players are selected from the correct seeds.

### Player Stats Sheet
Columns:
- Player ID
- Is Eliminated
- Player Name
- Position
- Team
- Team Seed
- Game ID
- Round
- Home Team
- Away Team
- Game Date
- Points
- Assists
- Rebounds
- Steals
- Blocks
- Turnovers
- Fouls
- Minutes Played
- Total Score (PTS+AST+REB)

This is your detailed stats sheet. Use VLOOKUP or formulas to calculate entry scores.

## Workflow

### Before Tournament
1. Fetch tournament bracket: `./ncaa-pool fetch-tournament --year 2026`
2. Fetch team rosters: `./ncaa-pool fetch-rosters --year 2026`
3. Export to sheets: `./ncaa-pool export --year 2026`
4. Participants fill out your Google Form to create entries

### During Tournament
Run daily (or after games):
1. Update stats: `./ncaa-pool update-stats --year 2026`
2. Export to sheets: `./ncaa-pool export --year 2026`
3. Your leaderboard formulas automatically update

## Automating Updates (Optional)

Set up a cron job to auto-update during the tournament:

```bash
# Edit crontab
crontab -e

# Add this line to update every 6 hours during March Madness
0 */6 * * * cd /home/dev/projects/ncaa-player-pool && ./ncaa-pool update-stats --year 2026 && ./ncaa-pool export --year 2026
```

## Troubleshooting

### "Credentials file not found"
- Check the path in GOOGLE_CREDENTIALS_FILE
- Use absolute path, not relative
- Ensure file has correct permissions

### "Failed to open spreadsheet"
- Verify GOOGLE_SHEET_ID is correct
- Ensure you shared the sheet with the service account email
- Check service account has Editor permissions

### "Permission denied"
- Service account needs **Editor** access (not just Viewer)
- Re-share the sheet with correct permissions

### "API not enabled"
- Enable Google Sheets API in Cloud Console
- Wait a few minutes for API to activate

## Security Notes

- **Never commit the service account JSON file to git!**
- Add it to `.gitignore`
- Store it securely on your server
- The service account only has access to sheets you explicitly share with it

## Sample Leaderboard Formula

In your Leaderboard sheet, you can use formulas like:

```
=SUMIF('Player Stats'!$C:$C, A2, 'Player Stats'!$T:$T)
```

Where:
- `'Player Stats'!$C:$C` = Player Name column
- `A2` = Player name from your entry
- `'Player Stats'!$T:$T` = Total Score column

This will automatically sum up the total score for each player in your entries!
