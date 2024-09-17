import pandas as pd
import requests
import xmltodict
from loguru import logger
from retry import retry

from my_board_games.settings import conf


@retry(tries=10, delay=3, backoff=2)
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
            #  numplays = int(item.get("numplays", "0")) # this one doesn't return right numbers
            if rating is not None:
                ratings.append(
                    {
                        "id": game_id,
                        "rating": rating,
                        #  "numplays": numplays,
                    }
                )
    if len(ratings) == 0:
        logger.error("No ratings found")
        raise ValueError("No ratings found")
    return ratings


def add_ratings(games, ratings):
    ratings_df = pd.DataFrame(ratings)
    games = games.merge(ratings_df, on="id", how="left", validate="many_to_one")
    return games
