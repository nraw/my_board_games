import pandas as pd


def get_suggested_players(games):
    game_players = games[["id", "name", "suggested_players"]]
    suggested_players = []
    for _, game in game_players.iterrows():
        for player_num, ratings in game["suggested_players"]["results"].items():
            if player_num.isdigit():
                is_ok = (
                    ratings["best_rating"]
                    + ratings["recommended_rating"]
                    - ratings["not_recommended_rating"]
                    > 0
                )
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
    return suggested_players
