"""Test marketplace listings fetching from BGG GeekMarket API."""

import json

from my_board_games.get_marketplace import get_marketplace_listings


def test_fetch_marketplace_listings():
    """Test fetching marketplace listings to see what data is available."""
    print("\n=== Fetching marketplace listings ===")

    # Fetch listings
    listings_df = get_marketplace_listings()

    print(f"\nFound {len(listings_df)} listings")


if __name__ == "__main__":
    test_fetch_marketplace_listings()
