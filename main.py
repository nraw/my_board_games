import json
from pathlib import Path

import pandas as pd
from boardgamegeek import BGGClient
from loguru import logger
from retry import retry

from my_board_games.get_metrics import get_metrics
#  from my_board_games.get_bbb_games import get_bbb_games
from my_board_games.get_ratings import add_ratings, get_personal_ratings
from my_board_games.get_sizes import add_sizes, get_sizes
from my_board_games.get_suggested_players import get_suggested_players
from my_board_games.logged_plays import add_logged_plays, get_logged_plays
from my_board_games.make_charts import make_charts
from my_board_games.settings import conf


def main():
    bgg = BGGClient()
    all_suggested_players = {}
    all_metrics = {}
    for user_name in conf["user_names"]:
        logger.info(f"Processing data for user: {user_name}")
        my_games = get_my_games(bgg, user_name)
        logger.info(f"Got {len(my_games)} games for user: {user_name}.")
        game_ids = my_games.id.to_list()
        logger.info("Getting games metadata")
        games = get_games(game_ids, bgg)
        logger.info("Got games metadata")
        logger.info("Add numplays")
        games = add_numplays(games, my_games)
        logger.info("Added numplays")
        logger.info("Getting logged plays")
        logged_plays = get_logged_plays(user_name)
        games = add_logged_plays(games, logged_plays)
        logger.info("Added logged plays to metadata")
        logger.info("Getting ratings")
        ratings = get_personal_ratings(user_name)
        games = add_ratings(games, ratings)
        logger.info("Added ratings to metadata")
        logger.info("Getting sizes")
        sizes = get_sizes(game_ids)
        games = add_sizes(games, sizes)
        logger.info("Added sizes to metadata")
        logger.info("Getting suggested players table")
        suggested_players = get_suggested_players(games)
        logger.info("Got suggested players table")
        logger.info("Create metrics")
        metrics = get_metrics()
        logger.info("Obtained metrics")
        all_suggested_players[user_name] = suggested_players.to_dict(orient="records")
        all_metrics[user_name] = metrics

    json.dump(all_suggested_players, open("data/suggested_players.json", "w"), default=str)
    json.dump(all_metrics, open("data/metrics.json", "w"))


def get_my_games(bgg, user_name) -> pd.DataFrame:
    exclude_list = conf["exclude_list"]
    games_batch = get_collection(
        bgg, user_name=user_name, own=True, exclude_subtype="boardgameexpansion"
    )
    games_info = {game.id: game._data for game in games_batch if "id" in dir(game)}
    my_games = pd.DataFrame(games_info).T
    my_games = my_games[my_games.own == "1"]
    my_games = my_games[~my_games.id.isin(exclude_list)]
    return my_games


def add_numplays(games, my_games):
    games = games.merge(
        my_games[["id", "numplays"]], on="id", how="left", validate="one_to_one"
    )
    return games


@retry(tries=10, delay=3, backoff=2)
def get_collection(bgg, **kwargs):
    collection = bgg.collection(**kwargs)
    return collection


def get_games(game_ids, bgg):
    games_batches = get_games_in_batches(game_ids, bgg)
    games_info = {game.id: game._data for game in games_batches if "id" in dir(game)}
    games = pd.DataFrame(games_info).T
    games["url"] = "https://boardgamegeek.com/boardgame/" + games["id"].astype("str")
    games["average_rating"] = games["stats"].apply(lambda x: x["average"])
    games["short_name"] = games["name"].apply(shorten_name)
    games = filter_quasi_expansions(games)
    return games


def get_games_in_batches(game_ids, bgg, batch_size=20):
    games_batches = []
    for i in range(0, len(game_ids), batch_size):
        batch = game_ids[i : i + batch_size]
        games_batch = get_games_batch(batch, bgg)
        games_batches.extend(games_batch)
    return games_batches


@retry(tries=10, delay=3, backoff=2)
def get_games_batch(batch, bgg):
    games_batch = bgg.game_list(batch)
    return games_batch


def shorten_name(name):
    short_name = name
    if ":" in short_name:
        short_name = short_name.split(":")[0]
    if len(short_name) > 20:
        short_name = "".join([word[0] for word in short_name.split()])
    return short_name


def filter_quasi_expansions(games):
    games = games[~games.name.isin(conf["mapping"].keys())]
    return games


if __name__ == "__main__":
    main()
