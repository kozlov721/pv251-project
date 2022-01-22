import dash
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from plotly.graph_objs._figure import Figure
import plotly.graph_objects as go

from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from typing import Optional, Final, Tuple, Set, List, Any, Dict, cast


class App:
    def __init__(self, data_path: str):
        self.STATES = {
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
        self.COLORS = ['#545ED2',
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

        self.FRAME: Final[pd.DataFrame] = cast(pd.DataFrame,
                                               pd.read_csv(data_path))
        self.MIN_SIZE: Final[int] = 0
        self.MAX_SIZE: Final[int] = self.FRAME['FIRE_SIZE'].max()
        self.MIN_YEAR: Final[int] = self.FRAME['FIRE_YEAR'].min()
        self.MAX_YEAR: Final[int] = self.FRAME['FIRE_YEAR'].max()
        self.YEARS: Final[List[int]] = list(
            range(self.MIN_YEAR, self.MAX_YEAR + 1))
        self.GEOFRAME: Final[pd.DataFrame] = self._make_geoframe()
        self.CAUSES: Final[List[str]] = self.FRAME['STAT_CAUSE_DESCR'].unique()

        self.states_filter: Set[str] = set()
        self.cause_filter: Set[str] = set()
        self.years_filter: Tuple[int, int] = (self.MAX_YEAR, self.MAX_YEAR)
        self.size_filter: Tuple[int, int] = (100, self.MAX_SIZE)
        self.full_map: Figure = self._make_map(
            self._filter_all(self.FRAME),
            self.GEOFRAME,
            focus=False
        )
        self.pie_chart: Figure = self._make_pie_charts(
            self._filter_all(self.FRAME, exclude=['STAT_CAUSE_DESCR'])
        )
        self.focused_map: Optional[Figure] = None

        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP]
        )

        def listen_events(self,
                          years: Tuple[int, int],
                          map_click,
                          pie_click,
                          *args) -> Tuple[Figure, Figure, str]:
            ctx = dash.callback_context
            trigger = ctx.triggered[0]['prop_id']
            redraw_full = redraw_pie = redraw_focused = False
            if trigger == 'year_range.value':
                redraw_full = redraw_pie = redraw_focused = True
                self.years_filter = years
            elif trigger == 'pie.clickData':
                self.cause_filter.add(pie_click['points'][0]['label'])
                redraw_full = redraw_focused = redraw_pie = True
            elif trigger == 'map.clickData':
                if (state := self._click_to_state(map_click)) is not None:
                    self.state_filter = state
                else:
                    raise PreventUpdate
                redraw_pie = redraw_focused = True
            elif trigger == 'zoom_back_button.n_clicks':
                redraw_pie = True
                self.state_filter = None
                self.focused_map = None
            elif trigger == 'reset_causes_button.n_clicks':
                redraw_pie = redraw_full = redraw_focused = True
                self.cause_filter.clear()
            return self._update_layout(redraw_pie, redraw_full, redraw_focused)

        self._listen_events = self.app.callback(
            [Output('map', 'figure'),
             Output('pie', 'figure'),
             Output('container', 'children')],
            [Input('year_range', 'value'),
             Input('map', 'clickData'),
             Input('pie', 'clickData'),
             Input('zoom_back_button', 'n_clicks'),
             Input('reset_causes_button', 'n_clicks')]
        )(lambda *args, **kwargs: listen_events(self, *args, **kwargs))

        self.app.layout = html.Div(children=[
            html.H1(
                children='Wildfires in the United States from 1992 to 2015.'
            ),
            dcc.RangeSlider(
                id='year_range',
                marks={i: str(i)
                       for i in range(self.MIN_YEAR, self.MAX_YEAR + 1)},
                min=self.MIN_YEAR,
                max=self.MAX_YEAR,
                value=[2015, 2015],
                allowCross=False
            ),
            html.Div([
                dbc.Button('Zoom back',
                           id='zoom_back_button',
                           className='me-1',
                           color='primary'),
                dbc.Button('Reset causes',
                           id='reset_causes_button',
                           className='me-1',
                           color='primary'),
            ]),
            html.Div(id='container', children='Focused on: Whole country'),

            dcc.Graph(id='map', figure=self.full_map),
            dcc.Graph(
                id='pie',
                figure=self.pie_chart
            )
        ])

    def _make_geoframe(self) -> pd.DataFrame:
        states = []
        for state in self.STATES:
            states.extend([state] * len(self.YEARS))
        return pd.DataFrame({
            'STATE': states,
            'FIRE_YEAR': self.YEARS * len(self.STATES)
        })

    def _update_layout(self,
                       redraw_pie: bool,
                       redraw_full: bool,
                       redraw_focused: bool
                       ) -> Tuple[Figure, Figure, str]:
        if not redraw_pie and not redraw_full and not redraw_focused:
            raise PreventUpdate
        if redraw_pie:
            self.pie_chart = self._make_pie_charts(
                self._filter_all(self.FRAME, exclude=['STAT_CAUSE_DESCR'])
            )
        if redraw_full:
            self.full_map = self._make_map(
                self._filter(
                    self.FRAME,
                    {'FIRE_YEAR': self.years_filter,
                     'STAT_CAUSE_DESCR': self.cause_filter,
                     'FIRE_SIZE': self.size_filter}
                ),
                self.GEOFRAME,
                focus=False
            )
        if redraw_focused:
            self.focused_map = self._make_map(
                self._filter_all(self.FRAME),
                self._filter(self.GEOFRAME, {'STATE': self.state_filter}),
                focus=True
            )
        if self.state_filter is None:
            message = 'Focused on: Whole country'
        else:
            message = f'Focused on: {self.STATES[self.state_filter]}'
        if self.focused_map is not None and self.state_filter is not None:
            return self.focused_map, self.pie_chart, message
        return self.full_map, self.pie_chart, message

    def _filter(self,
                df: pd.DataFrame,
                filters: Dict[str, Optional[Any]]) -> pd.DataFrame:

        for col, value in filters.items():
            if value is None:
                continue
            elif col == 'FIRE_YEAR' or col == 'FIRE_SIZE':
                min_, max_ = value
                df = df[(df[col] >= min_) &
                        (df[col] <= max_)]
            elif col == 'STAT_CAUSE_DESCR':
                if value:
                    bool_vector = df['STAT_CAUSE_DESCR'] == ''
                    for cause in value:
                        bool_vector |= df['STAT_CAUSE_DESCR'] == cause
                    df = df[bool_vector]
            else:
                df = df[df[col] == value]

        return df

    def _filter_all(self,
                    df: pd.DataFrame,
                    exclude: Optional[List] = None) -> pd.DataFrame:

        return self._filter(
            df,
            {col: fil for col, fil in [('FIRE_YEAR', self.years_filter),
                                       ('STATE', self.state_filter),
                                       ('STAT_CAUSE_DESCR', self.cause_filter),
                                       ('FIRE_SIZE', self.size_filter)]
             if exclude is None or col not in exclude
             }
        )

    def _make_map(self,
                  df: pd.DataFrame,
                  gf: pd.DataFrame,
                  focus: bool) -> Figure:

        fig = px.choropleth(
            gf,
            color='STATE',
            locations='STATE',
            color_discrete_map={state: '#EEEEFF' for state in self.STATES},
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

    def _make_pie_charts(self,
                         df: pd.DataFrame) -> Figure:

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
             for cause in self.CAUSES],
            [len(df[df['STAT_CAUSE_DESCR'] == cause])
             for cause in self.CAUSES]
        ]):

            fig.add_trace(
                go.Pie(
                    labels=self.CAUSES,
                    values=values,
                    hole=.4,
                    hoverinfo="label+percent",
                    textposition=calculateTextpositions(values),
                    marker_colors=self.COLORS
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

    @staticmethod
    def _click_to_state(click) -> Optional[str]:
        if (state := click['points'][0]['location']) is not None:
            return state
        return click['points'][0].get('customdata', [None])[0]

    def run_server(self, *args, **kwargs):
        self.app.run_server(*args, **kwargs)


if __name__ == '__main__':
    App('/home/martin/Disk/fires.csv').run_server(debug=True)
