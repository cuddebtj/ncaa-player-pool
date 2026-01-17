import json
import time
from pathlib import Path

import polars as pl


base_url = "https://api.sportradar.com/ncaamb/trial/v8/en/"
team_id = "267d417a-8f85-4c87-a15a-068c089a74c6"
tournament_url = base_url + "tournaments/56befd3f-4024-47c4-900f-892883cc1b6b/schedule.json"
game_url = base_url + "games/{game_id}/summary.json"
headers = {"accept": "application/json"}

with requests.Session() as session:
    if not Path("data/tournament_team_statistics.json").exists():
        session.headers = headers
        resp = session.get(tournament_url, params=api_key)
        resp.raise_for_status()
        tourney = resp.json()
        with open("data/tournament_team_statistics.json", "w") as f:
            json.dump(tourney, f, indent=4)
    else:
        with open("data/tournament_team_statistics.json", "r") as f:
            tourney = json.load(f)

    game_ids = []
    for round in tourney["rounds"]:
        print(round["name"])
        # if round["name"] not in ["First Four", "Final Four"]:
        #     for bracket in round["bracketed"]:
        #         for game in bracket["games"]:
        #             game_ids.append(game["id"])

        if round["name"] == "Final Four":
            for game in round["games"]:
                game_ids.append(game["id"])
        else:
            continue

    records = []
    for game in game_ids:
        time.sleep(2.5)
        resp = session.get(game_url.format(game_id=game), params=api_key)
        resp.raise_for_status()
        game_data = resp.json()
        with open(f"data/games/{game}.json", "w+") as f:
            json.dump(game_data, f, indent=4)

        home = game_data["home"]
        try:
            for player in home["players"]:
                try:
                    points = player["statistics"]["points"]
                except:
                    points = None
                try:
                    rebounds = player["statistics"]["rebounds"]
                except:
                    rebounds = None
                try:
                    assists = player["statistics"]["assists"]
                except:
                    assists = None
                record = {
                    "game_id": game,
                    "team_id": home["id"],
                    "team_name": home["market"],
                    "player_id": player["id"],
                    "player_name": player["full_name"],
                    "points": points,
                    "rebounds": rebounds,
                    "assists": assists,
                }
                records.append(record)

            away = game_data["away"]
            for player in away["players"]:
                try:
                    points = player["statistics"]["points"]
                except:
                    points = None
                try:
                    rebounds = player["statistics"]["rebounds"]
                except:
                    rebounds = None
                try:
                    assists = player["statistics"]["assists"]
                except:
                    assists = None
                record = {
                    "game_id": game,
                    "team_id": away["id"],
                    "team_name": away["market"],
                    "player_id": player["id"],
                    "player_name": player["full_name"],
                    "points": points,
                    "rebounds": rebounds,
                    "assists": assists,
                }
                records.append(record)
        except:
            continue

df = pl.from_dicts(records)
df.write_csv("./data/game_player_stats.csv")