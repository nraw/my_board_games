import altair as alt
import pandas as pd

from my_board_games.settings import conf


def make_time_since_last_played_chart(suggested_players):
    suggested_players_limited = suggested_players[suggested_players.players <= 8]
    suggested_players_limited = suggested_players_limited[
        ~suggested_players_limited.name.isin(conf["mapping"].keys())
    ]
    suggested_players_limited = suggested_players_limited[
        suggested_players_limited.players > 0
    ].copy()
    time_since_bins = [-1, 30, 90, 180, 365, 730, 1000]
    time_since_labels = [
        "In the last month",
        "In the last 3 months",
        "In the last 6 months",
        "In the last year",
        "In the last 2 years",
        "More than 2 years",
    ]
    suggested_players_limited["time_since_last_played"] = pd.cut(
        suggested_players_limited.days_since_last_played,
        time_since_bins,
        labels=time_since_labels,
    ).values.add_categories("Never")
    suggested_players_limited["time_since_last_played"] = suggested_players_limited[
        "time_since_last_played"
    ].fillna("Never")
    suggested_players_limited["days_since_last_played"] = suggested_players_limited[
        "days_since_last_played"
    ].fillna(9000)
    labels = time_since_labels + ["Never"]
    suggested_players_limited.sort_values(
        by=["time_since_last_played", "playingtime"], inplace=True
    )

    # https://github.com/altair-viz/altair/issues/963
    selection = alt.selection_single(
        fields=["time_since_last_played"], on="mouseover"  # , nearest=True
    )
    fig = (
        alt.Chart(suggested_players_limited)
        .mark_bar()
        .encode(
            x=alt.X("players:O", axis=alt.Axis(orient="top", labelAngle=0)),
            y=alt.Y(
                "count(id)", stack="zero", scale=alt.Scale(reverse=True), axis=None
            ),
            order=alt.Order("days_since_last_played:Q", sort="descending"),
            #  color="days_since_last_played:Q",
            color=alt.condition(
                selection,
                alt.Color("time_since_last_played:O", sort=labels),
                alt.value("lightgray"),
                legend=None,
            ),
            tooltip=[
                "name",
                "time_since_last_played",
                "days_since_last_played",
                "last_played",
                "playingtime",
            ],
            href="url",
        )
    )
    fig2 = (
        alt.Chart(suggested_players_limited)
        .mark_text(align="center", baseline="middle", dy=-10)
        .encode(
            x=alt.X("players:O", axis=alt.Axis(orient="top", labelAngle=0)),
            y=alt.Y(
                "count(id)", stack="zero", scale=alt.Scale(reverse=True), axis=None
            ),
            order=alt.Order("days_since_last_played:Q", sort="descending"),
            color=alt.condition(
                alt.datum.time_since_last_played == labels[-1],
                alt.value("white"),
                alt.value("black"),
            ),
            detail=["time_since_last_played", "days_since_last_played"],
            text="cool_name",
        )
    )
    fig = fig + fig2
    #  fig = alt.vconcat(fig1, fig2)
    fig = fig.add_selection(selection)
    return fig
