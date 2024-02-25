cat "average_chart.html" | sed 's/div id="vis"/div style="width: 98vw; height: 95vh" id="vis"/' > index.html
cat "last_played_chart.html" | sed 's/div id="vis"/div style="width: 98vw; height: 95vh" id="vis"/' > last_played.html
