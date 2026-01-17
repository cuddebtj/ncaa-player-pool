import time
from pathlib import Path

import httpx
import polars as pl

data_path = Path("data/2026/player_data.csv")
df = pl.read_csv(data_path)
team_ids = df[["team_id", "seed"]].unique().to_dicts()

base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
# team_url = base_url + "seasons/2024/REG/teams/{team_id}/statistics.json"
team_url = ""

headers = {"accept": "application/json"}

# with requests.Session() as session:
async with httpx.AsyncClient() as client:
    rows = []
    for team_row in team_ids:
        time.sleep(2.5)
        url =team_url.format(team_id=team_row["team_id"]) 
        # resp = session.get(url, params=api_key, headers=headers)
        resp = await client.get(url, params=api_key, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        for player in data["players"]:
            write_data = {
                "seed": team_row["seed"],
                "team_id": data["id"],
                "team_market": data["market"],
                "player_id": player["id"],
                "player_name": player["full_name"],
                "position": player["position"],
                "total_games_played": player["total"]["games_played"],
                "total_games_started": player["total"]["games_started"],
                "total_points": player["total"]["points"],
                "total_rebounds": player["total"]["rebounds"],
                "total_assists": player["total"]["assists"],
                "average_points": player["average"]["points"],
                "average_rebounds": player["average"]["rebounds"],
                "average_assists": player["average"]["assists"],
            }
            rows.append(write_data)

df = pl.from_dicts(rows)
df.write_csv("data/final_player_stats.csv", index=False)