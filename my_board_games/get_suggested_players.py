import pandas as pd


def get_suggested_players(games):
    game_players = games[["id", "name", "suggested_players"]]
    suggested_players = []
    for _, game in game_players.iterrows():
        for player_num, ratings in game["suggested_players"]["results"].items():
            is_ok = check_is_recommended_player_number(player_num, ratings)
            if is_ok:
                game_player = {
                    "id": game["id"],
                    "name": game["name"],
                    "players": int(player_num),
                }
                suggested_players += [game_player]
    suggested_players = pd.DataFrame(suggested_players)
    suggested_players = suggested_players.merge(
        games, on=["id", "name"], validate="m:1"
    )
    suggested_players = suggested_players.sort_values("average_rating", ascending=False)
    extra_rows = create_extra_rows(suggested_players)
    suggested_players = pd.concat([suggested_players, extra_rows])
    suggested_players['playingtime'] = suggested_players['playingtime'].astype('int')
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
