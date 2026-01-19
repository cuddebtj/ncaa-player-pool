# ESPN NCAA Basketball API Schema Documentation

This document describes the undocumented ESPN API structure for NCAA Men's College Basketball.

## Base URL
```
https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball
```

## Endpoints

### 1. Scoreboard
**URL:** `/scoreboard`
**Params:** `dates=YYYYMMDD` (optional)
**Purpose:** Get current/recent games

**Response Structure:**
```json
{
  "events": [
    {
      "id": "401827631",  // Game ID
      "date": "2026-01-19T01:00Z",
      "name": "Arizona State Sun Devils at Houston Cougars",
      "shortName": "ASU @ HOU",
      "competitions": [
        {
          "id": "401827631",
          "date": "2026-01-19T01:00Z",
          "attendance": 7055,
          "competitors": [
            {
              "id": "248",  // Team ID
              "homeAway": "home",
              "team": {
                "id": "248",
                "displayName": "Houston Cougars",
                "abbreviation": "HOU",
                "logo": "..."
              },
              "score": "74",
              "records": [...]
            },
            {
              "id": "9",  // Team ID
              "homeAway": "away",
              "team": {...},
              "score": "73"
            }
          ]
        }
      ]
    }
  ]
}
```

### 2. Game Summary
**URL:** `/summary?event={game_id}`
**Purpose:** Get detailed game info with box scores and player statistics

**Response Structure:**
```json
{
  "header": {
    "id": "401827631",
    "competitions": [
      {
        "date": "2026-01-19T01:00Z",
        "attendance": 7055,
        "competitors": [...]
      }
    ]
  },
  "boxscore": {
    "teams": [
      {
        "team": {
          "id": "9",
          "displayName": "Arizona State Sun Devils",
          "abbreviation": "ASU"
        },
        "statistics": [
          {"name": "fieldGoalsMade-fieldGoalsAttempted", "displayValue": "22-54"},
          {"name": "totalRebounds", "displayValue": "30"},
          {"name": "assists", "displayValue": "16"}
        ]
      }
    ],
    "players": [
      {
        "team": {
          "id": "9",
          "displayName": "Arizona State Sun Devils"
        },
        "statistics": [
          {
            "name": "Minutes Played",
            "keys": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
            "labels": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
            "athletes": [
              {
                "athlete": {
                  "id": "5176444",
                  "displayName": "Santiago Trouet",
                  "shortName": "S. Trouet",
                  "jersey": "1",
                  "position": {
                    "name": "Forward",
                    "abbreviation": "F"
                  }
                },
                "starter": true,
                "stats": [
                  "21",      // MIN
                  "9",       // FG (made-attempted is in display)
                  "2-6",     // FG
                  "0-1",     // 3PT
                  "5-6",     // FT
                  "3",       // OREB
                  "0",       // DREB
                  "2",       // REB
                  "2",       // AST
                  "0",       // STL
                  "2",       // BLK
                  "1",       // TO
                  "2"        // PTS
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**Important:** The `stats` array maps to the `keys` array. For our scoring:
- **Points (PTS):** Last element in stats array (index 12)
- **Rebounds (REB):** Index 6
- **Assists (AST):** Index 7

### 3. Team Info
**URL:** `/teams/{team_id}`
**Purpose:** Get team information

**Response Structure:**
```json
{
  "team": {
    "id": "248",
    "displayName": "Houston Cougars",
    "abbreviation": "HOU",
    "location": "Houston",
    "name": "Cougars",
    "slug": "houston-cougars",
    "color": "c8102e",
    "logos": [...],
    "record": {
      "items": [
        {"summary": "14-3", "stats": [...]}
      ]
    },
    "rank": 3
  }
}
```

**Note:** This endpoint does NOT include roster/players. Players are only available in game summaries.

### 4. Tournament Bracket (March Madness only)
**URL:** `/tournaments/{tournament_id}/summary.json`
**Tournament ID:** `56befd3f-4024-47c4-900f-892883cc1b6b` (NCAA Tournament)
**Purpose:** Get tournament bracket with seeds

**Availability:** Only available during March Madness tournament period.

**Expected Response Structure** (based on old data in `/data/2025/tournaments.json`):
```json
{
  "id": "56befd3f-4024-47c4-900f-892883cc1b6b",
  "name": "NCAA Men's Division I Basketball Tournament",
  "status": "inprogress",
  "brackets": [
    {
      "id": "...",
      "name": "East Regional",
      "participants": [
        {
          "id": "b18f34af-a7f1-4659-a2e5-fc11a31cd316",
          "name": "Saint Mary's Gaels",
          "market": "Saint Mary's",
          "seed": 3,
          "type": "team"
        }
      ],
      "games": [
        {
          "id": "...",
          "scheduled": "2025-03-20T20:00:00+00:00"
        }
      ]
    }
  ]
}
```

## Data Extraction Strategy

For the NCAA Player Pool application:

1. **During Regular Season (Now):**
   - Use `/scoreboard` to get current games
   - Use `/summary?event={game_id}` to get player stats
   - Extract player info from game summaries only (no roster endpoint)

2. **During March Madness:**
   - Use `/tournaments/{id}/summary.json` to get bracket with seeds
   - Extract team IDs and seeds from bracket
   - Use `/scoreboard?dates=YYYYMMDD` for specific tournament dates
   - Use `/summary?event={game_id}` for detailed player stats

3. **Player Roster Building:**
   - Build roster from accumulated game summary data
   - Players appear in boxscore -> players -> statistics -> athletes
   - Track unique players per team across all games

## Data Model Requirements

Based on API structure, we need:

### Tables:
- **teams**: id, name, abbreviation, seed (null for regular season), year
- **players**: id, name, team_id, position, jersey, year
- **games**: id, date, home_team_id, away_team_id, home_score, away_score, round_name
- **player_game_stats**: game_id, player_id, points, rebounds, assists, minutes, etc.

### Key Insights:
1. **No roster endpoint** - must build roster from game data
2. **Seeds only in tournament** - regular season teams don't have seeds
3. **Player stats format** - array mapped to keys, not object
4. **Tournament bracket** - only available during March Madness

## Rate Limiting
- ESPN API appears to be public/unauthenticated
- Implement 2.5 second delay between requests to be respectful
- Use retry logic with exponential backoff for failures
