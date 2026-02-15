"""Minimal tests for BGG API client."""

import pytest

from my_board_games.bgg_api import BGGClient, BGGItemNotFoundError, GameData


@pytest.fixture
def client():
    """Create a BGGClient instance."""
    return BGGClient()


def test_game_by_id(client):
    """Test fetching game data by ID using a well-known game."""
    # Use Gloomhaven (ID: 174430) as a stable test case
    game = client.game(game_id=174430)

    assert isinstance(game, GameData)
    assert game.id == 174430
    assert game.name == "Gloomhaven"
    assert game.min_players >= 1
    assert game.max_players >= game.min_players
    assert game.rating_average > 0
    assert isinstance(game.expansions, list)

    # Verify data dictionary structure
    data = game.data()
    assert "id" in data
    assert "name" in data
    assert "minplayers" in data
    assert "maxplayers" in data
    assert "stats" in data
    assert "suggested_players" in data


def test_game_not_found(client):
    """Test handling of non-existent game."""
    with pytest.raises(BGGItemNotFoundError):
        client.game(game_id=999999999)


def test_game_list(client):
    """Test fetching multiple games at once."""
    # Use two well-known games
    games = client.game_list([174430, 167791])  # Gloomhaven and Terraforming Mars

    assert len(games) == 2
    assert all(isinstance(game, GameData) for game in games)
    assert all(game.id in [174430, 167791] for game in games)
