import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from math import log10, pi, ceil
from plotly.graph_objs._figure import Figure
from plotly.subplots import make_subplots
from typing import Optional, Final, Tuple, List, Any, Dict, cast

MILE_WIDTH: Final[int] = 2800
MILE_HEIGHT: Final[int] = 1582

STATES = {
    'AL': 'Alabama',
    'AK': 'Alaska',
    'AZ': 'Arizona',
    'AR': 'Arkansas',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'IA': 'Iowa',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'ME': 'Maine',
    'MD': 'Maryland',
    'MA': 'Massachusetts',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MS': 'Mississippi',
    'MO': 'Missouri',
    'MT': 'Montana',
    'NE': 'Nebraska',
    'NV': 'Nevada',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NY': 'New York',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VT': 'Vermont',
    'VA': 'Virginia',
    'WA': 'Washington',
    'WV': 'West Virginia',
    'WI': 'Wisconsin',
    'WY': 'Wyoming',
    'DC': 'Washington, D.C.',
}
COLORS = ['#545ED2',
          '#C34936',
          '#04A880',
          '#9057D6',
          '#E38C59',
          '#25B3D2',
          '#DD5C86',
          '#A5C374',
          '#DB81D9',
          '#D6AB50',
          '#A9ACDA',
          '#D08E88',
          '#D10B12']

DATA_PATH: Final[str] = '/home/martin/Disk/fires.csv'
FRAME: Final[pd.DataFrame] = cast(pd.DataFrame, pd.read_csv(DATA_PATH))
WIDTH: Final[int] = 1000
HEIGHT: Final[int] = round(WIDTH * (MILE_HEIGHT / MILE_WIDTH))

# The constants are computed from some randomly chosen
# fire which I used as a reference point.
# This should scale the circles to have approximately
# the same area as the area of the corresponding fire.
RATIO: Final[float] = 1 / ((pi * (11.86 * (WIDTH / MILE_WIDTH)) ** 2) / 283180)

MIN_SIZE: Final[int] = 0
MAX_SIZE: Final[int] = FRAME['FIRE_SIZE'].max()
MIN_YEAR: Final[int] = FRAME['FIRE_YEAR'].min()
MAX_YEAR: Final[int] = FRAME['FIRE_YEAR'].max()

YEARS: Final[List[int]] = list(range(MIN_YEAR, MAX_YEAR + 1))
CAUSES: Final[List[str]] = list(FRAME['STAT_CAUSE_DESCR'].unique())


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)


def filter_frame(df: pd.DataFrame,
                 filters: Dict[str, Optional[Any]]) -> pd.DataFrame:

    for col, value in filters.items():
        if isinstance(value, tuple):
            min_, max_ = value
            df = df[(df[col] >= min_) &
                    (df[col] <= max_)]
        elif value and isinstance(value, list):
            bool_vector = df[col] != df[col]
            for cause in value:
                bool_vector |= df[col] == cause
            df = df[bool_vector]
        elif value and value is not None:
            df = df[df[col] == value]

    return df


def make_hover(info):
    name = str(info[0]).title()
    if name == 'NaN':
        name = '<i>no name</i>'
    size = round(info[1])
    state = STATES[info[2]]
    return (f'<b>State</b>: {state}<br>'
            f'<b>Name</b>: {name}<br>'
            f'<b>Size</b>: {size} ac')


def make_map(df: pd.DataFrame,
             states: Optional[List[str]],
             to_scale: bool) -> Figure:

    selected_states = states or list(STATES.keys())
    scatter = go.Scattergeo(
        lon=df['LONGITUDE'],
        lat=df['LATITUDE'],
        mode='markers',
        text=list(map(
            make_hover,
            zip(df['FIRE_NAME'], df['FIRE_SIZE'], df['STATE']))),
        hoverinfo='lon+lat+text',
        marker_color=df['FIRE_SIZE'],
        marker_size=df['FIRE_SIZE'],
        marker_sizeref=RATIO if to_scale else 1000,
        marker_sizemin=1,
        marker_sizemode='area',
        marker_opacity=0.6,
        marker_line_width=0,
        marker_cmin=MIN_SIZE,
        marker_cmax=MAX_SIZE,
        marker_colorbar=dict(title='Size')
    )

    choropleth = go.Choropleth(
        geo='geo',
        locationmode='USA-states',
        hoverinfo='skip',
        locations=list(selected_states),
        colorscale=[[0.0, (color := '#DDDDFF')], [1.0, color]],
        showlegend=False,
        z=[1] * len(selected_states),
        showscale=False,
        marker_line_color='#FFFFFF',
    )

    fig = cast(Figure, go.Figure(
        data=(scatter, choropleth),
        layout_width=WIDTH,
        layout_height=HEIGHT,
    ))

    if states:
        fig.update_geos(fitbounds='locations')

    fig.update_layout(
        geo_scope='usa',
        dragmode=False,
        margin={key: 0 for key in 'blrt'}
        )

    return fig


def make_pie_charts(df: pd.DataFrame) -> Figure:

    def calculateTextpositions(values):
        total = sum(values)
        if total == 0:
            return 'auto'
        return [
            'none' if value / total < 0.02 else 'auto'
            for value in values
        ]

    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{'type': 'domain'}, {'type': 'domain'}]],
        # specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=['Total Area', 'Number of incidents'])

    for i, values in enumerate([
        [sum(df[df['STAT_CAUSE_DESCR'] == cause]['FIRE_SIZE'])
         for cause in CAUSES],
        [len(df[df['STAT_CAUSE_DESCR'] == cause])
         for cause in CAUSES]
    ]):

        fig.add_trace(
            go.Pie(
                labels=CAUSES,
                values=values,
                hole=.4,
                hoverinfo="label+percent",
                textposition=calculateTextpositions(values),
                marker_colors=COLORS
            ),
            row=1,
            col=i + 1
        )

    fig.update_layout(height=HEIGHT,
                      width=WIDTH * 9 // 10,
                      title_text='Statistical causes of the fires')
    fig.update_layout(
        legend=dict(
            orientation='h'
        ),
        transition={'duration': 300, 'easing': 'cubic-in-out'}
    )

    assert isinstance(fig, Figure)
    return fig


@app.callback(
    [Output('map', 'figure'),
     Output('pie', 'figure')],
    [Input('year_range', 'value'),
     Input('size_range', 'value'),
     Input('state_dropdown', 'value'),
     Input('cause_dropdown', 'value'),
     Input('scale_switch', 'value')]
)
def listen_events(years: List[int],
                  sizes: List[float],
                  states: List[str],
                  causes: List[str],
                  scale: List[bool]) -> Tuple[Figure, Figure]:
    assert len(years) == len(sizes) == 2
    print(scale)
    def transform(x):
        return 0 if x == 0 else 10 ** (x - 1)
    # print(sizes[0], sizes[1])
    transformed_sizes = (transform(sizes[0]), transform(sizes[1]))
    # print(transformed_sizes)
    filtered_frame = filter_frame(
        FRAME,
        {
            'FIRE_YEAR': tuple(years),
            'FIRE_SIZE': transformed_sizes,
            'STAT_CAUSE_DESCR': causes,
            'STATE': states
        }
    )
    map_plot: Figure = make_map(
        filtered_frame,
        states,
        to_scale=bool(scale)
    )
    pie_chart: Figure = make_pie_charts(filtered_frame)

    return map_plot, pie_chart


app.layout = html.Div(children=[
    html.Br(),
    html.H1(
        children='Wildfires in the United States from 1992 to 2015',
        style={'text-align': 'center'}
    ),
    html.Div(id='selectors', children=[
        html.Div(id='sliders', children=[
            html.Label('Filter by years'),
            dcc.RangeSlider(
                id='year_range',
                marks={i: str(i)
                       for i in range(MIN_YEAR, MAX_YEAR + 1)},
                min=MIN_YEAR,
                max=MAX_YEAR,
                value=[2015, 2015],
                pushable=0
            ),

            html.Br(),
            html.Label('Filter by size'),
            dcc.RangeSlider(
                id='size_range',
                min=0,
                max=(logmax := ceil(log10(MAX_SIZE)) + 1),
                value=(log10(1000) + 1, logmax),
                pushable=0.1,
                step=0.1,
                marks={0: '0'} | {(i + 1): str(10 ** i) for i in range(logmax + 1)}
            )
        ], style={'padding': 10, 'flex': 1}),
        html.Div(id='dropdown', children=[
            html.Label('Select states'),
            dcc.Dropdown(
                id='state_dropdown',
                options=[
                    {'label': state_name, 'value': state_code}
                    for state_code, state_name in STATES.items()
                ],
                multi=True,
                value=[],
            ),

            html.Br(),
            html.Label('Filter by the cause of the fire'),
            dcc.Dropdown(
                id='cause_dropdown',
                options=[
                    {'label': cause, 'value': cause}
                    for cause in CAUSES
                ],
                multi=True,
                value=[]
            ),
            html.Br(),
            dbc.Checklist(
                id='scale_switch',
                switch=True,
                options=[{'label': 'Show to scale', 'value': True}],
                value=[]
            )
        ], style={'padding': 10, 'flex': 1})
    ], style={'display': 'flex', 'flex-direction': 'row'}),
    html.Div(id='graphs', children=[
        dcc.Graph(id='map'),
        dcc.Graph(id='pie'),
    ], style={'display': 'flex', 'flex-direction': 'row'})
])

if __name__ == '__main__':
    app.run_server(debug=True)
