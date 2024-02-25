import altair as alt

from my_board_games.charts.average_rating_chart import \
    make_average_rating_chart
from my_board_games.charts.time_since_last_played_chart import \
    make_time_since_last_played_chart


def make_charts(suggested_players):
    fig = make_average_rating_chart(suggested_players)
    filename = "average_chart.html"
    save_chart(fig, filename)
    fig2 = make_time_since_last_played_chart(suggested_players)
    filename = "last_played_chart.html"
    save_chart(fig2, filename)

    return fig


def save_chart(fig, filename):
    fig = fig.properties(width="container", height="container").configure_view(
        strokeWidth=0
    )
    fig.save(filename, embed_options={"actions": False})
