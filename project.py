import json
import dash
import pandas as pd
import plotly.express as px
# import dash_leaflet as dl


from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash_extensions.javascript import assign


app = dash.Dash(__name__)

frame = pd.read_csv('fires.csv')

assert isinstance(frame, pd.DataFrame)

frame = frame[frame['FIRE_SIZE'] >= 100]
STATES = {
    "Alabama":              "AL",
    "Alaska":               "AK",
    "Arizona":              "AZ",
    "Arkansas":             "AR",
    "California":           "CA",
    "Colorado":             "CO",
    "Connecticut":          "CT",
    "Delaware":             "DE",
    "Florida":              "FL",
    "Georgia":              "GA",
    "Hawaii":               "HI",
    "Idaho":                "ID",
    "Illinois":             "IL",
    "Indiana":              "IN",
    "Iowa":                 "IA",
    "Kansas":               "KS",
    "Kentucky":             "KY",
    "Louisiana":            "LA",
    "Maine":                "ME",
    "Maryland":             "MD",
    "Massachusetts":        "MA",
    "Michigan":             "MI",
    "Minnesota":            "MN",
    "Mississippi":          "MS",
    "Missouri":             "MO",
    "Montana":              "MT",
    "Nebraska":             "NE",
    "Nevada":               "NV",
    "New Hampshire":        "NH",
    "New Jersey":           "NJ",
    "New Mexico":           "NM",
    "New York":             "NY",
    "North Carolina":       "NC",
    "North Dakota":         "ND",
    "Ohio":                 "OH",
    "Oklahoma":             "OK",
    "Oregon":               "OR",
    "Pennsylvania":         "PA",
    "Rhode Island":         "RI",
    "South Carolina":       "SC",
    "South Dakota":         "SD",
    "Tennessee":            "TN",
    "Texas":                "TX",
    "Utah":                 "UT",
    "Vermont":              "VT",
    "Virginia":             "VA",
    "Washington":           "WA",
    "West Virginia":        "WV",
    "Wisconsin":            "WI",
    "Wyoming":              "WY"
}

geojson_url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
geojson_filter = assign("function(feature, context){return context.props.hideout == feature.id;}")


def get_center(df):
    lon_min = df['LONGITUDE'].min()
    lon_max = df['LONGITUDE'].max()
    lat_min = df['LATITUDE'].min()
    lat_max = df['LATITUDE'].max()
    return {'lat': (lat_min + lat_max) / 2,
            'lon': (lon_min + lon_max) / 2}


CENTERS = {
    state: get_center(frame[frame['STATE_NAME'] == state])
    for state in STATES
}

# with open('./geo.json', 'r', encoding='utf-8') as file:
    # geojson = json.load(file)


app.layout = html.Div(children=[
    html.H1(children='Wildfires in the United States from 1992 to 2015.'),
    dcc.Dropdown(id='slct_state',
                 options=[
                     {'label': name, 'value': name}
                     for name in STATES
                 ],
                 multi=False,
                 placeholder='Select a state'),
    dcc.Checklist(
        id='is_year_range',
        options=[
            {'label': 'Custom year range', 'value': 'True'},
        ],
        value=['True']
    ),
    dcc.RangeSlider(
        id='year_range',
        marks={i: str(i) for i in range(1992, 2016)},
        min=1992,
        max=2015,
        value=[1992, 2015]
    ),
    html.Div(id='container', children=[]),

    dcc.Graph(id='graph')
])


@app.callback(
    [Output(component_id='graph', component_property='figure'),
     Output(component_id='container', component_property='children')],
    [Input(component_id='slct_state', component_property='value'),
     Input(component_id='year_range', component_property='value')]
)
def update_graph(state, years):
    df = frame.copy()
    container = f'Chosen state: {state}'
    min_year, max_year = years
    if state is not None:
        df = df[df['STATE_NAME'] == state]

    fig_scatter = px.scatter_geo(df, lat='LATITUDE', lon='LONGITUDE', scope='usa',
                                 color="FIRE_SIZE", size='FIRE_SIZE', size_max=20, opacity=0.6,
                                 width=1000, height=700, hover_data=['FIRE_NAME', 'FIRE_SIZE', 'STATE'],
                                 animation_frame='YEAR')

    fig_scatter.update_traces(marker=dict(line=dict(width=0)),
                              selector=dict(mode='markers'))

    if state is not None:

        fig = px.choropleth(df, scope='usa', locations='STATE_NAME', color='STATE',
                            color_discrete_map={state: '#EEEEFF' for state in STATES.values()},
                            geojson='https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json',
                            width=1000, height=700, animation_frame='YEAR',
                            featureidkey='properties.name')
        if fig_scatter.data:
            fig.add_trace(
                fig_scatter.data[0]
            )

        for i in range(len(fig.frames)):
            fig.frames[i].data += (fig_scatter.frames[i].data[0],)

        fig.update_geos(fitbounds='locations')

        return fig, container

    return fig_scatter, container


if __name__ == '__main__':
    app.run_server(debug=True)
