import pandas as pd
import requests
import xmltodict

from my_board_games.settings import conf


def get_personal_ratings():
    username = conf["user_name"]
    ratings = []
    #  url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&rated=1&stats=1"
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&own=1&stats=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = xmltodict.parse(response.content)
        items = data["items"]["item"]
        for item in items:
            #  game_name = item["name"]["#text"]
            game_id = int(item["@objectid"])
            rating = item.get("stats", {}).get("rating", None).get("@value", None)
            numplays = item.get("numplays", "0")
            if rating is not None:
                ratings.append(
                    {
                        "id": game_id,
                        "rating": rating,
                        "numplays": numplays,
                    }
                )

    return ratings


def add_ratings(games, ratings):
    ratings_df = pd.DataFrame(ratings)
    games = games.merge(ratings_df, on="id", how="left", validate="many_to_one")
    return games
