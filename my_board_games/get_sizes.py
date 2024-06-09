import pandas as pd
from boardgamegeek import BGGClient
from retry import retry
from tqdm import tqdm


def get_sizes(game_ids):
    bgg = BGGClient()
    games_sizes = [get_game_size_data(bgg, game_id) for game_id in tqdm(game_ids)]
    sizes = pd.concat([get_size(g) for g in games_sizes])
    sizes = sizes.reset_index()
    return sizes


@retry(tries=10, delay=3, backoff=2)
def get_game_size_data(bgg, game_id):
    g = bgg.game(game_id=game_id, versions=True)
    return g


def get_size(g):
    versions = g.data()["versions"]
    games_df = pd.DataFrame(versions)
    games_df["game"] = g.name
    games_df["game_id"] = g.id
    games_df["size"] = games_df["width"] + games_df["length"] + games_df["depth"]
    games_df["size"] = games_df["width"] * games_df["length"] * games_df["depth"]
    games_df["size"] = games_df["size"].astype(int)

    games_with_size = games_df[games_df["size"] > 0]
    if len(games_with_size):
        games_df = games_with_size

    english_games_df = games_df[games_df.language == "English"]
    if len(english_games_df):
        games_df = english_games_df

    game_df = games_df[games_df["size"] == games_df["size"].max()].iloc[:1]
    return game_df


def add_sizes(games, sizes):
    sizes_df = sizes.copy()
    sizes_df = sizes_df[["game_id", "size"]]
    sizes_df.columns = ["id", "size"]
    games = games.merge(sizes_df, on="id", how="left", validate="many_to_one")
    return games
