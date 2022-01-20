import dash
from pprint import pprint
import pandas as pd
import plotly.express as px


from dash import dcc
from dash import html
from dash.dependencies import Input, Output


app = dash.Dash(__name__)

frame = pd.read_csv('fires.csv')

assert isinstance(frame, pd.DataFrame)

frame = frame[frame['FIRE_SIZE'] >= 100]
STATES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming"
}


years = list(range(1992, 2016))
states = list(STATES.keys())
sts = []
for state in states:
    sts.extend([state] * len(years))
geoframe = pd.DataFrame({
    'STATE': sts,
    'YEAR': years * len(states)

})


def make_graph(df, gf, focus):
    fig = px.choropleth(
        gf,
        color='STATE',
        locations='STATE',
        color_discrete_map={state: '#EEEEFF' for state in STATES},
        locationmode="USA-states", scope="usa",
        width=1000,
        height=700)

    fig.update_layout(showlegend=False)
    fig.update_traces(
        hovertemplate=None,
        hoverinfo='none'
    )

    fig_scatter = px.scatter_geo(df,
                                 lat='LATITUDE',
                                 lon='LONGITUDE',
                                 hover_data=['STATE'],
                                 color="FIRE_SIZE",
                                 size='FIRE_SIZE',
                                 size_max=20,
                                 opacity=0.6,
                                 width=1000,
                                 height=700,
                                 range_color=[0, 606945])

    if focus:
        fig.update_geos(fitbounds='locations')
    else:
        fig.update_geos(visible=False)

    fig_scatter.update_traces(marker=dict(line=dict(width=0)),
                              selector=dict(mode='markers'))

    if fig_scatter.data:
        fig.add_trace(
            fig_scatter.data[0]
        )

    fig.layout['coloraxis'] = fig_scatter.layout['coloraxis']

    return fig


def filter_year(df, min_year, max_year):
    return df[(df['YEAR'] >= min_year) & (df['YEAR'] <= max_year)]


DEFAULT_GRAPH = make_graph(
    filter_year(frame, 2015, 2015),
    filter_year(geoframe, 2015, 2015),
    False)

app.layout = html.Div(children=[
    html.H1(children='Wildfires in the United States from 1992 to 2015.'),
    dcc.RangeSlider(
        id='year_range',
        marks={i: str(i) for i in range(1992, 2016)},
        min=1992,
        max=2015,
        value=[2015, 2015],
        allowCross=False
    ),
    html.Button('Zoom back', id='button'),
    html.Div(id='container', children=[]),

    dcc.Graph(id='graph', figure=DEFAULT_GRAPH)
])


last_click = None
prev_years = (2015, 2015)


@app.callback(
    [Output('graph', 'figure'),
     Output('container', 'children')],
    [Input('year_range', 'value'),
     Input('graph', 'clickData'),
     Input('button', 'n_clicks')]
)
def update_graph(years, click, button):
    global last_click
    global prev_years
    global DEFAULT_GRAPH
    if years != prev_years:
        DEFAULT_GRAPH = make_graph(
            filter_year(frame, *years),
            filter_year(geoframe, *years),
            False)
    pprint(click)
    ctx = dash.callback_context
    # print(ctx.triggered)
    # print(ctx.states)
    # print(ctx.inputs)
    if click is None or ctx.triggered[0]['prop_id'] == 'button.n_clicks':
        if ctx.triggered[0]['prop_id'] != 'year_range.value':
            return DEFAULT_GRAPH, 'Whole country'

    if ((location := click['points'][0]['location']) is not None
            or (location := click['points'][0]
                .get('customdata', [None])[0]) is not None):

        state = location
    else:
        raise dash.exceptions.PreventUpdate

    if state == last_click:
        last_click = None
        return DEFAULT_GRAPH, 'Whole country'
    else:
        last_click = state

    df = filter_year(frame[frame['STATE'] == state], *years)
    gf = filter_year(geoframe[geoframe['STATE'] == state], *years)
    container = f'Chosen state: {state}'

    return make_graph(df, gf, True), container


if __name__ == '__main__':
    app.run_server(debug=True)
