import pandas as pd
import requests
import xmltodict
from loguru import logger
from retry import retry

from my_board_games.settings import conf


@retry(tries=10, delay=3, backoff=2)
def get_personal_ratings(user_name):
    ratings = []
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={user_name}&own=1&stats=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = xmltodict.parse(response.content)
        items = data["items"]["item"]
        for item in items:
            game_id = int(item["@objectid"])
            rating = item.get("stats", {}).get("rating", None).get("@value", None)
            if rating is not None:
                ratings.append(
                    {
                        "id": game_id,
                        "rating": rating,
                    }
                )
    if len(ratings) == 0:
        logger.error(f"No ratings found for user: {user_name}")
        raise ValueError(f"No ratings found for user: {user_name}")
    return ratings


def add_ratings(games, ratings):
    ratings_df = pd.DataFrame(ratings)
    games = games.merge(ratings_df, on="id", how="left", validate="many_to_one")
    return games
