"""Fetch marketplace listings for games from BoardGameGeek."""

import pandas as pd
from loguru import logger
from retry import retry

from my_board_games.bgg_api import BGGClient
from my_board_games.settings import conf


@retry(tries=10, delay=3, backoff=2, logger=logger)
def get_marketplace_listings():
    """Fetch marketplace listings from BGG GeekMarket.

    Returns:
        DataFrame with columns: id, name, price, currency, condition, product_id, link
    """
    bgg = BGGClient()
    user_name = conf["user_name"]

    logger.info(f"Fetching marketplace listings for user: {user_name}")
    try:
        listings = bgg.marketplace_listings(user_name)
    except Exception as e:
        logger.error(f"Error fetching marketplace listings: {e}")
        raise

    if not listings:
        logger.warning("No marketplace listings found")
        return pd.DataFrame(
            columns=["id", "name", "price", "currency", "condition", "product_id", "link"]
        )

    df = pd.DataFrame(listings)
    logger.info(f"Found {len(df)} marketplace listings")

    return df


def add_marketplace_prices(games, marketplace_listings):
    """Add marketplace price information to games DataFrame.

    Args:
        games: DataFrame with game information
        marketplace_listings: DataFrame with marketplace listings

    Returns:
        DataFrame with added marketplace columns
    """
    if marketplace_listings.empty:
        games["marketplace_price"] = None
        games["marketplace_currency"] = None
        games["marketplace_condition"] = None
        games["marketplace_link"] = None
        return games

    # Merge marketplace data with games
    games = games.merge(
        marketplace_listings[["id", "price", "currency", "condition", "link"]],
        on="id",
        how="left",
        validate="one_to_many",
    )

    # Rename columns for clarity
    games = games.rename(
        columns={
            "price": "marketplace_price",
            "currency": "marketplace_currency",
            "condition": "marketplace_condition",
            "link": "marketplace_link",
        }
    )

    # Log how many games have marketplace prices
    games_with_prices = games["marketplace_price"].notna().sum()
    logger.info(f"Added marketplace prices to {games_with_prices} games")

    return games
