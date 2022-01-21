import dash
from pprint import pprint
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from plotly.graph_objs._figure import Figure
import plotly.graph_objects as go


from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from typing import Optional, Tuple, List, Union, Any, Dict, cast

app = dash.Dash(__name__)

frame = cast(pd.DataFrame, pd.read_csv('/home/martin/Disk/fires.csv'))
MIN_YEAR = frame['FIRE_YEAR'].min()
MAX_YEAR = frame['FIRE_YEAR'].max()

frame = frame[frame['FIRE_SIZE'] >= 100]

PIE_LABELS = [
    'Structure',
    'Powerline',
    'Children',
    'Campfire',
    'Miscellaneous',
    'Railroad',
    'Debris Burning',
    'Lightning',
    'Smoking',
    'Missing/Undefined',
    'Equipment Use',
    'Fireworks',
    'Arson'
]

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


years = list(range(1992, 2016))
states = list(STATES.keys())
sts = []
for state in states:
    sts.extend([state] * len(years))
geoframe = pd.DataFrame({
    'STATE': sts,
    'FIRE_YEAR': years * len(states)

})


def filter_year(df: pd.DataFrame,
                min_year: int,
                max_year: int) -> pd.DataFrame:
    return df[(df['FIRE_YEAR'] >= min_year) & (df['FIRE_YEAR'] <= max_year)]


def filter_frame(df: pd.DataFrame,
                 filters: Dict[str, Optional[Any]]) -> pd.DataFrame:

    for col, value in filters.items():
        if value is None:
            continue
        if col == 'FIRE_YEAR':
            df = filter_year(df, *value)
        else:
            df = df[df[col] == value]

    return df


def filter_frames(df: pd.DataFrame,
                  gf: pd.DataFrame,
                  filters: Dict[str, Optional[Any]]
                  ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return tuple(filter_frame(frame, filters) for frame in [df, gf])


def make_map(df: pd.DataFrame,
             gf: pd.DataFrame,
             focus: bool) -> Figure:

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

    fig_scatter = px.scatter_geo(
        df,
        lat='LATITUDE',
        lon='LONGITUDE',
        hover_data=['STATE', 'STAT_CAUSE_DESCR'],
        color="FIRE_SIZE",
        size='FIRE_SIZE',
        size_max=20,
        opacity=0.6,
        width=1000,
        height=700,
        range_color=[0, 606945]
    )

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
    fig.update_layout(
        dragmode=False,
        transition={'duration': 300, 'easing': 'cubic-in-out'}
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

    fig.add_trace(
        go.Pie(
            labels=PIE_LABELS,
            values=(total_area := [
                sum(df[df['STAT_CAUSE_DESCR'] == cause]['FIRE_SIZE'])
                for cause in PIE_LABELS
            ]),
            name='Total Area',
            textposition=calculateTextpositions(total_area)
            ),
        1,
        1
    )
    fig.add_trace(
        go.Pie(
            labels=PIE_LABELS,
            values=(total_count := [
                len(df[df['STAT_CAUSE_DESCR'] == cause])
                for cause in PIE_LABELS
            ]),
            name='Number of Fire Area',
            textposition=calculateTextpositions(total_count)
            ),
        1,
        2
    )
    fig.update_traces(hole=.4, hoverinfo="label+percent")
    fig.update_layout(height=600,
                      width=1000,
                      title_text='Statistical causes of the fires')
    fig.update_layout(
        legend=dict(
            orientation="h"
        ),
        transition={'duration': 300, 'easing': 'cubic-in-out'}
    )

    assert isinstance(fig, Figure)
    return fig


curr_years: Tuple[int, int] = (MAX_YEAR, MAX_YEAR)
curr_cause: Optional[str] = None
focused_state: Optional[str] = None

DEFAULT_GRAPH = make_map(
    filter_year(frame, *curr_years),
    filter_year(geoframe, *curr_years),
    False,
)

app.layout = html.Div(children=[
    html.H1(children='Wildfires in the United States from 1992 to 2015.'),
    dcc.RangeSlider(
        id='year_range',
        marks={i: str(i) for i in range(MIN_YEAR, MAX_YEAR + 1)},
        min=MIN_YEAR,
        max=MAX_YEAR,
        value=[2015, 2015],
        allowCross=False
    ),
    html.Button('Zoom back', id='button'),
    html.Div(id='container', children=[]),

    dcc.Graph(id='map', figure=DEFAULT_GRAPH),
    dcc.Graph(id='pie',
              figure=make_pie_charts(filter_year(frame, *curr_years)))
])


def update_years(years) -> Tuple[Figure, Figure, str]:
    global DEFAULT_GRAPH
    global curr_years
    curr_years = years
    df = filter_year(frame, *curr_years)
    DEFAULT_GRAPH = make_map(
        df,
        geoframe,
        False
    )
    if focused_state is not None:
        df = filter_frame(
            df,
            {
                'STATE': focused_state,
                'STAT_CAUSE_DESCR': curr_cause
            }
        )
        return (
            make_map(
                df,
                filter_frame(geoframe, {'STATE': focused_state}),
                True
            ),
            make_pie_charts(df),
            f'Focused on: {STATES[focused_state]}')
    return DEFAULT_GRAPH, make_pie_charts(df), 'Whole country'


def update_causes(cause: str) -> Tuple[Figure, Figure, str]:
    global curr_cause
    if curr_cause == cause:
        curr_cause = None
    else:
        curr_cause = cause
    print(curr_cause)
    print(len(frame))
    df = filter_frame(
        frame,
        {
            'STATE': focused_state,
            'FIRE_YEAR': curr_years
        }
    )

    gf = filter_frame(geoframe, {'STATE': focused_state})
    print(len(df))

    return (make_map(filter_frame(df, {'STAT_CAUSE_DESCR': curr_cause}),
                     gf,
                     focused_state is not None),
            make_pie_charts(df),
            f'Focused on: {STATES.get(str(focused_state), "Whole country")}')


def focus_graph(state) -> Tuple[Figure, Figure, str]:
    global focused_state
    if state == focused_state:
        raise dash.exceptions.PreventUpdate

    focused_state = state

    df = filter_frame(
        frame,
        {
            'STATE': focused_state,
            'STAT_CAUSE_DESCR': curr_cause,
            'FIRE_YEAR': curr_years
        }
    )
    gf = filter_frame(geoframe, {'STATE': focused_state})

    assert focused_state is not None
    return (make_map(df, gf, True,),
            make_pie_charts(df),
            f'Focused on: {STATES[focused_state]}')


def get_state_from_click(click) -> Optional[str]:
    if (state := click['points'][0]['location']) is not None:
        return state
    return click['points'][0].get('customdata', [None])[0]


@app.callback(
    [Output('map', 'figure'),
     Output('pie', 'figure'),
     Output('container', 'children')],
    [Input('year_range', 'value'),
     Input('map', 'clickData'),
     Input('pie', 'clickData'),
     Input('button', 'n_clicks')]
)
def update_graph(years: Tuple[int, int],
                 click, pie_click,
                 button: int) -> Tuple[Figure, Figure, str]:
    global focused_state
    global curr_cause
    ctx = dash.callback_context
    # print(ctx.triggered)
    # print(ctx.states)
    # print(ctx.inputs)
    if ctx.triggered[0]['prop_id'] == 'year_range.value':
        return update_years(years)
    if ctx.triggered[0]['prop_id'] == 'pie.clickData':
        return update_causes(pie_click['points'][0]['label'])
    if ctx.triggered[0]['prop_id'] == 'map.clickData':
        if (state := get_state_from_click(click)) is not None:
            return focus_graph(state)
        raise dash.exceptions.PreventUpdate
    if ctx.triggered[0]['prop_id'] == 'button.n_clicks':
        focused_state = curr_cause = None
        return (DEFAULT_GRAPH,
                make_pie_charts(filter_year(frame, *curr_years)),
                'Whole country')
    raise dash.exceptions.PreventUpdate


if __name__ == '__main__':
    app.run_server(debug=True)
