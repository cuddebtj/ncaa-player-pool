import time
from pathlib import Path

import requests
import polars as pl
import pandas as pd

data_path = Path("data\player_data.csv")
df = pl.read_csv(data_path)
team_ids = df[["team_id", "seed"]].unique().to_dicts()

base_url = "https://api.sportradar.com/ncaamb/trial/v8/en/"
team_url = base_url + "seasons/2024/REG/teams/{team_id}/statistics.json"
api_key = {"api_key": "bkmdR8b2OXyilWKmWp5UB01WbYfxjqTyGJow6BZz"}

headers = {"accept": "application/json"}

with requests.Session() as session:
    rows = []
    for team_row in team_ids:
        time.sleep(2.5)
        url =team_url.format(team_id=team_row["team_id"]) 
        resp = session.get(url, params=api_key, headers=headers)
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
            # df = pd.DataFrame.from_dict(write_data)
            # df.to_csv("data/player_stats.csv", header=False, index=False, mode="a")
            rows.append(write_data)

df = pd.DataFrame.from_records(rows)
df.to_csv("data/final_player_stats.csv", index=False)