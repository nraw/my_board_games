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

    # Fetch wishlist games
    logger.info(f"Fetching wishlist for {user_name}")
    wishlist_collection = bgg.collection(user_name=user_name, wishlist=True, exclude_subtype="boardgameexpansion")
    wishlist_ids = {item.id for item in wishlist_collection}
    logger.info(f"Found {len(wishlist_ids)} wishlist games")

    # Build personal ratings, ownership, and numplays lookup from all collections
    personal_ratings = {}
    owned_ids = set()
    numplays_lookup = {}
    for item in owned_collection:
        if item._data.get("own_status"):
            owned_ids.add(item.id)
        if item._data.get("personal_rating") is not None:
            personal_ratings[item.id] = item._data["personal_rating"]
        numplays_lookup[item.id] = item._data.get("numplays", 0)
    for item in rated_collection:
        if item._data.get("own_status"):
            owned_ids.add(item.id)
        if item._data.get("personal_rating") is not None:
            personal_ratings[item.id] = item._data["personal_rating"]
        if item.id not in numplays_lookup:
            numplays_lookup[item.id] = item._data.get("numplays", 0)
    for item in wishlist_collection:
        if item._data.get("personal_rating") is not None:
            personal_ratings.setdefault(item.id, item._data["personal_rating"])
        if item.id not in numplays_lookup:
            numplays_lookup[item.id] = item._data.get("numplays", 0)

    # Combine all game IDs
    all_game_ids = {item.id for item in owned_collection} | rated_ids | wishlist_ids
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

        stats = data.get("stats", {})
        weight = stats.get("averageweight")
        playingtime = data.get("playingtime")
        minplayers = data.get("minplayers")
        maxplayers = data.get("maxplayers")

        if game_id in owned_ids:
            status = "owned"
        elif game_id in wishlist_ids:
            status = "wishlist"
        else:
            status = "rated"

        games_data.append({
            "id": game_id,
            "name": data["name"],
            "thumbnail": data.get("thumbnail"),
            "mechanics": [m["name"] for m in mechanics],
            "bgg_rating": round(bgg_rating, 2) if bgg_rating else None,
            "personal_rating": personal_rating,
            "status": status,
            "weight": round(weight, 2) if weight else None,
            "playingtime": playingtime if playingtime else None,
            "minplayers": minplayers,
            "maxplayers": maxplayers,
            "numplays": numplays_lookup.get(game_id, 0),
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

    owned_count = sum(1 for g in games_data if g["status"] == "owned")
    wishlist_count = sum(1 for g in games_data if g["status"] == "wishlist")
    rated_only = sum(1 for g in games_data if g["status"] == "rated")
    with_personal = sum(1 for g in games_data if g["personal_rating"] is not None)
    logger.info(
        f"Wrote {len(games_data)} games ({owned_count} owned, {wishlist_count} wishlist, "
        f"{rated_only} rated-only) and {len(all_mechanics)} mechanics to {output_path}. "
        f"{with_personal} games have personal ratings."
    )

    return result


if __name__ == "__main__":
    user_name = sys.argv[1] if len(sys.argv) > 1 else conf["user_name"]
    get_mechanics(user_name)
