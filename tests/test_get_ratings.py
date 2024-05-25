from my_board_games.get_ratings import *


def test_get_ratings():
    ratings = get_personal_ratings()
    assert isinstance(ratings, list)
    assert len(ratings) > 0
    assert isinstance(ratings[0], dict)
    assert "id" in ratings[0]
    assert "rating" in ratings[0]
    assert "numplays" in ratings[0]

