# Google Sheets Integration

Export player data and statistics to Google Sheets.

## Setup

### 1. Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable the Google Sheets API
4. Create a service account
5. Download the JSON credentials file

### 2. Create Spreadsheet

Create a new Google Sheets spreadsheet and note the ID from the URL:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

### 3. Share with Service Account

Share the spreadsheet with the service account email:

1. Click "Share" button
2. Add the service account email (from JSON file)
3. Give "Editor" access

### 4. Configure Environment

```bash
GOOGLE_CREDENTIALS_FILE=/path/to/service-account.json
GOOGLE_SHEET_ID=your_spreadsheet_id
```

## Export Command

```bash
./ncaa-pool export --year 2026
```

## Sheet Structure

The app creates/updates these sheets:

### Players

| Column | Description |
|--------|-------------|
| Player ID | ESPN player identifier |
| Name | Full player name |
| Team | Team name |
| Seed | Tournament seed |
| Position | Player position |

### Player Stats

| Column | Description |
|--------|-------------|
| Player ID | Player identifier |
| Name | Player name |
| Team | Team name |
| Games | Games played |
| Points | Total points |
| Rebounds | Total rebounds |
| Assists | Total assists |
| Score | PTS + REB + AST |

## Custom Leaderboard

Create your own "Leaderboard" sheet with formulas:

```text
=SUMIF('Player Stats'!$A:$A, B2, 'Player Stats'!$H:$H)
```

Where B2 contains a player ID from the Entries sheet.
