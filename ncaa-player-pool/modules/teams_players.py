import json
import time

import polars as pl


base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
tournament_url = base_url + "tournaments/56befd3f-4024-47c4-900f-892883cc1b6b/summary.json"
team_url = base_url + "teams/{team_id}/profile.json"

headers = {"accept": "application/json"}
player_data = []


with requests.Session() as session:
    session.headers = headers
    resp = session.get(tournament_url, params=api_key)
    resp.raise_for_status()
    tourney = resp.json()
    school_ids = []
    with open("data/tournaments.json", "w") as f:
        json.dump(tourney, f, indent=4)

    for bracket in tourney["brackets"]:
        for school in bracket["participants"]:
            school_ids.append((school["id"], school["seed"]))

    for id, seed in school_ids:
        team_resp = session.get(
            team_url.format(team_id=id), 
            headers=headers, 
            params=api_key
        )
        team_resp.raise_for_status()
        team_json = team_resp.json()
        # team_name = team_json["name"]
        print(team_json["name"])
        team_market = team_json["market"]
        for player in team_json["players"]:
            player_id = player["id"]
            player_name = player["full_name"]
            player_dict = {
                "seed": seed,
                "team_id": id,
                "team_name": team_market,
                "player_id": player_id,
                "player_name": player_name,
            }
            player_data.append(player_dict)

        time.sleep(2.5)

df = pl.from_dicts(player_data)
df.write_csv("data/player_data.csv")