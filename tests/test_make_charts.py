from my_board_games.make_charts import *


def test_average_rating_chart():
    import pandas as pd

    suggested_players = pd.read_csv("data/suggested_players.csv")
    fig = make_average_rating_chart(suggested_players)
    fig = fig.properties(width=1800, height=1000).configure_view(strokeWidth=0)
    fig.save("data/fig.html")


def test_time_since_last_played_chart():
    import pandas as pd

    suggested_players = pd.read_csv("data/suggested_players.csv")
    fig = make_time_since_last_played_chart(suggested_players)
    fig = fig.properties(width=1800, height=1000).configure_view(strokeWidth=0)
    fig.save("data/fig2.html")
