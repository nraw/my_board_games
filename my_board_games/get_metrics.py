import json


def get_metrics():
    suggested_players = json.load(open("data/suggested_players.json"))
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
        max([g["days_since_last_played"] for g in played_games]) if played_games else 0
    )
    gain_from_max_played = max_days_since_last_played / len(played_games)

    # Marketplace statistics
    games_for_sale = [g for g in owned_games if g.get("marketplace_price")]
    num_games_for_sale = len(games_for_sale)
    total_marketplace_value = (
        sum([g["marketplace_price"] for g in games_for_sale]) if games_for_sale else 0
    )
    average_marketplace_price = (
        total_marketplace_value / num_games_for_sale if num_games_for_sale > 0 else 0
    )
    most_expensive_game = (
        max(games_for_sale, key=lambda x: x["marketplace_price"])["name"]
        if games_for_sale
        else None
    )
    most_expensive_price = (
        max(games_for_sale, key=lambda x: x["marketplace_price"])["marketplace_price"]
        if games_for_sale
        else 0
    )

    metrics = dict(
        num_games=num_games,
        game_last_played=game_last_played,
        game_played_latest=game_played_latest,
        average_days_since_last_played=average_days_since_last_played,
        max_days_since_last_played=max_days_since_last_played,
        gain_from_max_played=gain_from_max_played,
        num_games_for_sale=num_games_for_sale,
        total_marketplace_value=total_marketplace_value,
        average_marketplace_price=average_marketplace_price,
        most_expensive_game=most_expensive_game,
        most_expensive_price=most_expensive_price,
    )
    json.dump(metrics, open("data/metrics.json", "w"))
    return metrics
