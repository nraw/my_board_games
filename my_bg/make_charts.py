import altair as alt


def make_charts(suggested_players):

    # https://github.com/altair-viz/altair/issues/963
    selection = alt.selection_single(
        fields=["playingtime"], on="mouseover"  # , nearest=True
    )
    fig = (
        alt.Chart(suggested_players)
        .mark_bar()
        .encode(
            x=alt.X("players:O", axis=alt.Axis(orient="top", labelAngle=0)),
            y=alt.Y("count(id)", scale=alt.Scale(reverse=True), axis=None),
            order=alt.Order("playingtime", sort="descending"),
            color=alt.condition(
                selection, "average_rating", alt.value("lightgray"), legend=None
            ),
            tooltip=["name", "playingtime", "average_rating"],
        )
    )
    #  fig = alt.vconcat(fig1, fig2)
    fig = fig.add_selection(selection)
    fig = fig.properties(width="container", height="container").configure_view(
        strokeWidth=0
    )
    fig.save("index2.html", embed_options={"actions": False})
    return fig
