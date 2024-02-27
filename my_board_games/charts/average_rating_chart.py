import altair as alt


def make_average_rating_chart(suggested_players):
    suggested_players_limited = suggested_players[suggested_players.players <= 8]

    # https://github.com/altair-viz/altair/issues/963
    selection = alt.selection_single(
        fields=["playingtime"], on="mouseover"  # , nearest=True
    )
    fig = (
        alt.Chart(suggested_players_limited)
        .mark_bar()
        .encode(
            x=alt.X("players:O", axis=alt.Axis(orient="top", labelAngle=0)),
            y=alt.Y(
                "count(id)", stack="zero", scale=alt.Scale(reverse=True), axis=None
            ),
            order=alt.Order("playingtime", sort="descending"),
            color=alt.condition(
                selection, "average_rating:Q", alt.value("lightgray"), legend=None
            ),
            tooltip=["name", "playingtime", "average_rating", "description"],
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
            order=alt.Order("playingtime", sort="descending"),
            color=alt.condition(
                alt.datum.average_rating > 7.5, alt.value("white"), alt.value("black")
            ),
            detail="average_rating",
            text="cool_name",
        )
    )
    fig = fig + fig2
    #  fig = alt.vconcat(fig1, fig2)
    fig = fig.add_selection(selection)
    return fig
