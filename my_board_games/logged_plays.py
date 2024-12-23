import xml.etree.ElementTree as ET

import pandas as pd
import requests

from my_board_games.settings import conf


def get_logged_plays(user_name):
    # API endpoint for retrieving plays data
    url = f"https://www.boardgamegeek.com/xmlapi2/plays?username={user_name}&page="

    # Retrieve all pages of plays data
    page_num = 1
    plays_list = []
    while True:
        response = requests.get(url + str(page_num))
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            plays = root.findall(".//play")
            if len(plays) == 0:
                break
            for play in plays:
                play_data = {
                    "date": play.get("date"),
                    "quantity": play.get("quantity"),
                    "game_id": play.get("id"),
                    "game_name": play.find(".//item").get("name"),
                }
                plays_list.append(play_data)
            page_num += 1
        else:
            print(
                "Failed to retrieve plays data. Please check your username and try again."
            )
            break

    # Create a Pandas DataFrame from the plays data
    logged_plays = pd.DataFrame(plays_list)
    logged_plays["game_name"] = logged_plays["game_name"].apply(map_duplicates)
    return logged_plays


def add_logged_plays(games, logged_plays):
    last_played = logged_plays.groupby("game_name").date.max().reset_index()
    last_played.columns = ["name", "last_played"]
    games = games.merge(last_played, on="name", how="left")
    games = get_days_since_last_played(games)
    return games


def get_days_since_last_played(games):
    games["last_played"] = pd.to_datetime(games["last_played"])
    games["days_since_last_played"] = (
        pd.to_datetime("today") - games["last_played"]
    ).dt.days
    return games


def map_duplicates(name):
    mapping = conf["mapping"]
    if name in mapping:
        name = mapping[name]
    return name
