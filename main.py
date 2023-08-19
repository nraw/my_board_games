import json

import pandas as pd
from boardgamegeek import BGGClient
from loguru import logger
from retry import retry

#  from my_bg.get_bbb_games import get_bbb_games
from my_bg.get_suggested_players import get_suggested_players
from my_bg.make_charts import make_charts
from my_bg.settings import conf


def main():
    bgg = BGGClient()
    logger.info("Getting games")
    my_games = get_my_games(bgg)
    #  bbb_games = get_bbb_games()
    logger.info(f"Got {len(my_games)} games.")
    game_ids = my_games.id.to_list()
    logger.info("Getting games metadata")
    games = get_games(game_ids, bgg)
    logger.info("Got games metadata")
    logger.info("Getting suggested players table")
    suggested_players = get_suggested_players(games)
    logger.info("Got suggested players table")
    logger.info("Charting")
    make_charts(suggested_players)
    logger.info("Charted")


def get_my_games(bgg) -> pd.DataFrame:
    exclude_list = conf["exclude_list"]
    games_batch = get_collection(
        bgg, user_name="nraw", own=True, exclude_subtype="boardgameexpansion"
    )
    games_info = {game.id: game._data for game in games_batch if "id" in dir(game)}
    my_games = pd.DataFrame(games_info).T
    my_games = my_games[my_games.own == "1"]
    my_games = my_games[~my_games.id.isin(exclude_list)]
    return my_games


@retry(tries=10, delay=3, backoff=2)
def get_collection(bgg, **kwargs):
    collection = bgg.collection(**kwargs)
    return collection


def get_games(game_ids, bgg):
    games_batch = bgg.game_list(game_ids)
    games_info = {game.id: game._data for game in games_batch if "id" in dir(game)}
    games = pd.DataFrame(games_info).T
    games["url"] = "https://boardgamegeek.com/boardgame/" + games["id"].astype("str")
    games["average_rating"] = games["stats"].apply(lambda x: x["average"])
    games["short_name"] = games["name"].apply(shorten_name)
    return games


def shorten_name(name):
    short_name = name
    if ":" in short_name:
        short_name = short_name.split(":")[0]
    if len(short_name) > 20:
        short_name = "".join([word[0] for word in short_name.split()])
    return short_name


if __name__ == "__main__":
    main()
