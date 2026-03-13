"""Fetch all mechanics for a user's BGG collection and rated games, dump to JSON."""

import json
import sys

from loguru import logger

from my_board_games.bgg_api import BGGClient
from my_board_games.settings import conf


def get_mechanics(user_name: str) -> dict:
    """Fetch collection + rated games and extract mechanics with ratings."""
    bgg = BGGClient()

    # Fetch owned games
    logger.info(f"Fetching owned collection for {user_name}")
    owned_collection = bgg.collection(user_name=user_name, own=True, exclude_subtype="boardgameexpansion")
    logger.info(f"Found {len(owned_collection)} owned games")

    # Fetch rated games (includes games not owned)
    logger.info(f"Fetching rated games for {user_name}")
    rated_collection = bgg.collection(user_name=user_name, rated=True, exclude_subtype="boardgameexpansion")
    rated_ids = {item.id for item in rated_collection}
    logger.info(f"Found {len(rated_ids)} rated games")

    # Build personal ratings and ownership lookup from both collections
    personal_ratings = {}
    owned_ids = set()
    for item in owned_collection:
        if item._data.get("own_status"):
            owned_ids.add(item.id)
        if item._data.get("personal_rating") is not None:
            personal_ratings[item.id] = item._data["personal_rating"]
    for item in rated_collection:
        if item._data.get("own_status"):
            owned_ids.add(item.id)
        if item._data.get("personal_rating") is not None:
            personal_ratings[item.id] = item._data["personal_rating"]

    # Combine all game IDs
    all_game_ids = {item.id for item in owned_collection} | rated_ids
    exclude_list = conf.get("exclude_list", [])
    game_ids = [gid for gid in all_game_ids if gid not in exclude_list]
    logger.info(f"Total unique games (after exclusions): {len(game_ids)}")

    # Fetch game details in batches
    all_games = []
    batch_size = 20
    for i in range(0, len(game_ids), batch_size):
        batch = game_ids[i : i + batch_size]
        logger.info(f"Fetching batch {i // batch_size + 1} ({len(batch)} games)")
        games = bgg.game_list(batch)
        all_games.extend(games)

    # Build mechanics data
    games_data = []
    all_mechanics = {}
    for game in all_games:
        data = game.data()
        mechanics = data.get("mechanics", [])
        game_id = data["id"]
        bgg_rating = data.get("stats", {}).get("average")
        personal_rating = personal_ratings.get(game_id)

        games_data.append({
            "id": game_id,
            "name": data["name"],
            "thumbnail": data.get("thumbnail"),
            "mechanics": [m["name"] for m in mechanics],
            "bgg_rating": round(bgg_rating, 2) if bgg_rating else None,
            "personal_rating": personal_rating,
            "owned": game_id in owned_ids,
        })
        for m in mechanics:
            all_mechanics[m["name"]] = m["id"]

    result = {
        "user": user_name,
        "games": games_data,
        "mechanics": [{"id": mid, "name": name} for name, mid in sorted(all_mechanics.items())],
    }

    output_path = "data/mechanics.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    owned_count = sum(1 for g in games_data if g["owned"])
    rated_only = sum(1 for g in games_data if not g["owned"])
    with_personal = sum(1 for g in games_data if g["personal_rating"] is not None)
    logger.info(
        f"Wrote {len(games_data)} games ({owned_count} owned, {rated_only} rated-only) "
        f"and {len(all_mechanics)} mechanics to {output_path}. "
        f"{with_personal} games have personal ratings."
    )

    return result


if __name__ == "__main__":
    user_name = sys.argv[1] if len(sys.argv) > 1 else conf["user_name"]
    get_mechanics(user_name)
