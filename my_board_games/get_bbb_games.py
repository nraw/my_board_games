from functools import lru_cache

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.utils import quote
from tqdm import tqdm

tqdm.pandas()


def get_bbb_games(bgg):
    url = "http://bohemiaboardsandbrews.com/games"
    res = requests.get(url)
    res_html = res.text

    bs = BeautifulSoup(res_html, "lxml")
    games_raw = bs.find_all("div", class_="game_rollover")
    games = clean_games(games_raw)
    games["id"] = games.game.progress_apply(lambda x: get_bgg_id(x, bgg))
    bbb_games = games[games.id.apply(lambda x: type(x) == str)]
    return bbb_games


def clean_games(games_raw):
    games = pd.DataFrame([game.text for game in games_raw], columns=["raw_game"])
    games["czech"] = games.raw_game.str.contains("\(CZ\)")
    games = games[~games.czech].copy()
    games["brackets"] = games.raw_game.str.extract("(\(.*\))")
    games["game"] = games.raw_game.str.extract("(.*)\(")
    games["game"] = games.apply(
        lambda x: x["raw_game"] if np.isnan(x["game"]) else x["game"], axis=1
    )
    games["game"] = games.game.str.strip()
    #  whatever = games.iloc[:89].game.progress_apply(get_bgg_id)
    return games


@lru_cache(1000)
def get_bgg_id(game, bgg):
    try:
        bgg_id = bgg.game(game).id
    except Exception:
        bgg_id = None
    return bgg_id


@lru_cache(1000)
def get_bgg_id2(query):
    try:
        encoded_query = quote(query)
        url = f"https://wishlist-scanner.herokuapp.com/barcode2bgg/{encoded_query}"
        res = requests.get(url)
        bgg_id = res.json()
    except:
        bgg_id = None
    return bgg_id


def adhoc():
    bbb_backup = bbb_games.copy()
    bbb_backup_ids = bbb_backup[["id", "name"]]
    bbb_backup_ids.columns = ["id2", "game"]
    games = games.merge(bbb_backup_ids, on="game", how="left")
    games["id"] = games.apply(
        lambda x: str(int(x["id"])) if not np.isnan(x["id"]) else x["id2"], axis=1
    )
    games = games.merge(my_games[["game", "id"]], how="left").drop_duplicates()
    games["id"] = games.progress_apply(
        lambda x: get_bgg_id2(x["game"]) if x["id"] is None else x["id"], axis=1
    )
