import json


def get_metrics(suggested_players):
    owned_games = [g for g in suggested_players if g["is_best_player"]]
    num_games = len(owned_games)
    played_games = [g for g in owned_games if g["last_played"]]
    played_games.sort(key=lambda x: x["last_played"], reverse=True)
    game_last_played = played_games[0]["name"] if played_games else None
    game_played_latest = played_games[-1]["name"] if played_games else None
    average_days_since_last_played = (
        sum([g["days_since_last_played"] for g in played_games]) / len(played_games)
        if played_games
        else None
    )
    max_days_since_last_played = (
        max([g["days_since_last_played"] for g in played_games])
        if played_games
        else None
    )
    metrics = dict(
        num_games=num_games,
        game_last_played=game_last_played,
        game_played_latest=game_played_latest,
        average_days_since_last_played=average_days_since_last_played,
        max_days_since_last_played=max_days_since_last_played,
    )
    json.dump(metrics, open("data/metrics.json", "w"))
    return metrics
