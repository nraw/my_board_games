import json
from pathlib import Path

import pandas as pd


def get_suggested_players(games):
    game_players = games[["id", "name", "suggested_players"]]
    suggested_players = []
    for _, game in game_players.iterrows():
        best_player_count = get_best_player_count(game)
        for player_num, ratings in game["suggested_players"]["results"].items():
            is_best_player = player_num == best_player_count
            is_ok = check_is_recommended_player_number(player_num, ratings)
            if is_ok:
                game_player = {
                    "id": game["id"],
                    "name": game["name"],
                    "players": int(player_num),
                    "best_player_count": best_player_count,
                    "is_best_player": is_best_player,
                }
                suggested_players += [game_player]
    suggested_players = pd.DataFrame(suggested_players)
    suggested_players = suggested_players.merge(
        games, on=["id", "name"], validate="m:1"
    )
    suggested_players = suggested_players.sort_values("average_rating", ascending=False)
    extra_rows = create_extra_rows(suggested_players)
    suggested_players = pd.concat([suggested_players, extra_rows])
    suggested_players["playingtime"] = suggested_players["playingtime"].astype("int")
    suggested_players["cool_name"] = get_cool_names(suggested_players)
    Path("data/suggested_players.json").write_text(
        suggested_players.to_json(orient="records")
    )
    return suggested_players


def check_is_recommended_player_number(player_num, ratings):
    is_ok = False
    is_player_num = player_num.isdigit()
    if is_player_num:
        is_ok = (
            ratings["best_rating"]
            + ratings["recommended_rating"]
            - ratings["not_recommended_rating"]
            > 0
        )
    return is_ok


def get_best_player_count(game):
    player_counts_dict = game["suggested_players"]["results"]
    best_player_count = max(
        player_counts_dict.keys(), key=lambda x: player_counts_dict[x]["best_rating"]
    )
    return best_player_count


def create_extra_rows(suggested_players):
    extra_rows = pd.DataFrame(
        suggested_players["playingtime"].drop_duplicates().sort_values(ascending=False)
    )
    extra_rows["id"] = extra_rows["playingtime"]
    extra_rows["name"] = extra_rows["playingtime"].astype("str") + " minutes"
    extra_rows["players"] = 0
    extra_rows["average_rating"] = suggested_players["average_rating"].min()
    extra_rows["short_name"] = extra_rows["name"]
    return extra_rows


def get_cool_names(suggested_players):
    cool_names = suggested_players.apply(get_cool_name, axis=1)
    return cool_names


def get_cool_name(game):
    cool_name = game["short_name"]
    if game["is_best_player"]:
        cool_name = "🔸 " + cool_name
    return cool_name
