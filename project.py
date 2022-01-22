import dash
import pandas as pd
from plotly.subplots import make_subplots
from plotly.graph_objs._figure import Figure
import plotly.graph_objects as go
from math import pi

from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from typing import Optional, Final, Tuple, Set, List, Any, Dict, cast

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
    'WY': 'Wyoming'
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
m2p_ratio = WIDTH / MILE_WIDTH
RATIO: Final[float] = 1 / ((pi * (11.86 * m2p_ratio) ** 2) / 283180)
MIN_SIZE: Final[int] = 0
MAX_SIZE: Final[int] = FRAME['FIRE_SIZE'].max()
MIN_YEAR: Final[int] = FRAME['FIRE_YEAR'].min()
MAX_YEAR: Final[int] = FRAME['FIRE_YEAR'].max()
YEARS: Final[List[int]] = list(
    range(MIN_YEAR, MAX_YEAR + 1))
CAUSES: Final[List[str]] = FRAME['STAT_CAUSE_DESCR'].unique()


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)


def filter_frame(df: pd.DataFrame,
                 filter_frames: Dict[str, Optional[Any]]) -> pd.DataFrame:

    for col, value in filter_frames.items():
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


def make_map(df: pd.DataFrame, states: Optional[List[str]]) -> Figure:
    selected_states = states or list(STATES.keys())
    scatter = go.Scattergeo(
        lon=df['LONGITUDE'],
        lat=df['LATITUDE'],
        mode='markers',
        text=df['FIRE_NAME'].map(lambda x: 'Fire name: ' + str(x).title()),
        hoverinfo='lon+lat+text',
        marker_color=df['FIRE_SIZE'],
        marker_size=df['FIRE_SIZE'],
        marker_sizeref=RATIO,
        marker_sizemin=1,
        marker_sizemode='area',
        marker_opacity=0.6,
        marker_line_width=0,
        marker_cmin=0,
        marker_cmax=606945,
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
        1,
        2,
        specs=[[{'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=['Total Area', 'Number of incidents'])

    for col, values in enumerate([
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
            1,
            col + 1
        )

    fig.update_layout(height=600,
                      width=1000,
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
     Input('state_dropdown', 'value'),
     Input('cause_dropdown', 'value')]
)
def listen_events(years: List[int],
                  states: List[str],
                  causes: List[str]) -> Tuple[Figure, Figure]:
    print(years, states, causes)
    assert len(years) == 2
    map_plot: Figure = make_map(
        filter_frame(
            FRAME,
            {
                'FIRE_YEAR': tuple(years),
                'FIRE_SIZE': (500, MAX_SIZE),
                'STAT_CAUSE_DESCR': causes,
                'STATE': states
            }
        ),
        states
    )
    pie_chart: Figure = make_pie_charts(
        filter_frame(
            FRAME,
            {
                'FIRE_YEAR': tuple(years),
                'FIRE_SIZE': (500, MAX_SIZE),
                'STAT_CAUSE_DESCR': causes,
                'STATE': states
            }
        )
    )

    return map_plot, pie_chart


app.layout = html.Div(children=[
    html.H1(
        children='Wildfires in the United States from 1992 to 2015.'
    ),
    html.Div(id='selectors', children=[
        dcc.RangeSlider(
            id='year_range',
            marks={i: str(i)
                   for i in range(MIN_YEAR, MAX_YEAR + 1)},
            min=MIN_YEAR,
            max=MAX_YEAR,
            value=[2015, 2015],
            allowCross=False,
        ),
        dcc.Dropdown(
            id='state_dropdown',
            options=[
                {'label': state_name, 'value': state_code}
                for state_code, state_name in STATES.items()
            ],
            multi=True,
            value=[],
        ),
        dcc.Dropdown(
            id='cause_dropdown',
            options=[
                {'label': cause, 'value': cause}
                for cause in CAUSES
            ],
            multi=True,
            value=[]
        ),
    ]),
    dcc.Graph(id='map'),
    dcc.Graph(id='pie'),
])

if __name__ == '__main__':
    app.run_server(debug=True)
