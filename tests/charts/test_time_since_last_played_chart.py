from my_board_games.charts.time_since_last_played_chart import *


def test_last_played_chart():
    import pandas as pd

    suggested_players = pd.read_csv("data/suggested_players.csv")
    fig = make_time_since_last_played_chart(suggested_players)
    fig = fig.properties(width=1800, height=1000).configure_view(strokeWidth=0)
    fig.save("data/fig2.html")
