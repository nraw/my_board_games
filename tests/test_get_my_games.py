from types import SimpleNamespace

from main import get_my_games
from my_board_games.settings import conf


class FakeBGG:
    def __init__(self, games):
        self.games = games

    def collection(self, **kwargs):
        return [
            SimpleNamespace(id=game_id, _data={"id": game_id, "name": name})
            for game_id, name in self.games
        ]


def test_location_si_games_are_configured():
    assert set(conf["location_si"]) == {194655, 160477, 242343}


def test_get_my_games_excludes_location_si_games():
    bgg = FakeBGG(
        [
            (194655, "Santorini"),
            (160477, "Onitama"),
            (242343, "Siege Storm"),
            (174430, "Gloomhaven"),
        ]
    )

    my_games = get_my_games(bgg)

    assert my_games.name.to_list() == ["Gloomhaven"]
