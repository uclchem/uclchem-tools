import pandas as pd
import yaml
import numpy as np
import plotly.graph_objects as go
from tqdm import tqdm

from uclchem_tools import (
    plot_rates,
    plot_rates_comparison,
    plot_abundances_comparison,
    plot_abundances_comparison2,
)
from uclchem_tools.viz.process import process_data

# Dash things:
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, dcc, Input, Output, State
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate


# Data loading and handling


def analyze_rates(data, specie):
    d1 = process_data(data, specie)
    return plot_rates(**d1)


class lazy_df_dict:
    def __init__(
        self,
        h5root,
        key,
        walker,
    ):
        self.h5root = h5root
        self.key = key
        self.walker = walker
        self.values_dict = {}

    def __getitem__(self, key):
        if not isinstance(self.values_dict[key], pd.DataFrame):
            with pd.HDFStore(self.h5root, complevel=9, complib="zlib") as store:
                self.values_dict[key] = store.get(f"{self.walker}/{key}")
        return self.values_dict[key]

    def __setitem__(self, key, value):
        self.values_dict[key] = value

    def keys(self):
        return self.values_dict.keys()

    def values(self):
        return self.values_dict.values()


def load_data(h5root):
    # Lazy loading non-leaves gives weird behaviour.
    lazy_level = 2
    with pd.HDFStore(h5root, complevel=9, complib="zlib") as store:
        read_dict = {}
        for walker in tqdm(store.walk("/")):
            # walker: (root, children, leaves)
            # Walk throught the levels of the dictionary to walk the h5 tree:
            access_read_dict = read_dict
            # We need to filter the root "/" for better behaviour
            dict_path = walker[0][1:].split("/")
            if dict_path != [""]:
                for key in dict_path:
                    access_read_dict = access_read_dict[key]
            # Create the children of the node
            for key in walker[1]:
                # Only lazy load the deeper datasets (since there are many!)
                if len(dict_path) >= lazy_level:
                    access_read_dict[key] = lazy_df_dict(
                        h5root, key, f"{walker[0]}/{key}"
                    )
                else:
                    access_read_dict[key] = {}
            # Create the leaf nodes, which are dataframes.
            for key in walker[2]:
                if len(dict_path) >= lazy_level:
                    access_read_dict[key] = f"{walker[0]}/{key}"
                else:
                    access_read_dict[key] = store.get(f"{walker[0]}/{key}")

            # print(f"root: {walker[0]}, keys: {walker[1]}, datasets: {walker[2]}" )
    return read_dict


def get_unique_elements(data_dict):
    all_elements = []
    for df in data_dict.values():
        for data_keys in df:
            all_elements.append(df[data_keys]["abundances"].columns.values)
    all_elements = list(np.unique(np.concatenate(all_elements)))
    print(all_elements)
    for spec in all_elements:
        if spec.startswith("#") and spec.replace("#", "$") not in all_elements:
            all_elements.append(spec.replace("#", "$"))
        elif spec.startswith("@") and spec.replace("@", "$") not in all_elements:
            all_elements.append(spec.replace("@", "$"))

    [
        all_elements.remove(nonspecies)
        for nonspecies in [
            "Time",
            "Density",
            "gasTemp",
            "av",
            "zeta",
            "point",
            "radfield",
        ]
    ]
    return all_elements


# More dash things:


def get_fig0(names_to_display):
    names_to_display += ["Collapsing Cloud", "Hot Core", "Static Cloud"]
    fig = plot_abundances_comparison(
        df_dict,
        names_to_display,
        # ["H2+", "H2", "CO", "H3+"],
        list(df_dict.keys()),
        list(df_dict.keys())[0],
        verbose=False,
        plot_temp=True,
    )
    return fig


if __name__ == "__main__":
    # Data loading part:
    paths = ["comparison/v3.1/test-store.h5", "comparison/v3.2/test-store.h5"]
    data = [load_data(path) for path in paths]
    df_dict = {k: v for k, v in zip(paths, data)}
    # Load all possible species keys
    all_keys = get_unique_elements(df_dict)
    names_to_display = ["H", "H2", "$H", "H2O", "$H2O", "CO", "$CO", "$CH3OH", "CH3OH"]
    fig = get_fig0(names_to_display)
    # names = [d.name for d in fig.data]
    figdropdown = dcc.Dropdown(
        options=all_keys,
        value=names_to_display,
        id="my-multi-dynamic-dropdown",
        multi=True,
    )
    # refresh_fig(fig, names, names_to_display=names_to_display)
    fig.update_layout(
        height=1200,
    )
    button = html.Div(
        [
            dbc.Button("Refresh", id="example-button", className="me-2", n_clicks=0),
            html.Span(id="example-output", style={"verticalAlign": "middle"}),
        ]
    )

    fig1 = plot_rates_comparison(
        data[0]["phase1Full"]["rates"], data[1]["phase1Full"]["rates"], "CH3OH"
    )
    fig1.update_layout(title_text="Phase 1")

    fig2 = plot_abundances_comparison2(
        [data[0]["phase1Full"]["abundances"], data[1]["phase1Full"]["abundances"]],
        ["CH3OH2+", "$CH3OH", "CH3OH"],
        plot_temp=True,
    )
    fig2.update_layout(title_text="Phase 1")

    # Dash things:
    app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

    @app.callback(
        Output("my-multi-dynamic-dropdown", "options"),
        Input("my-multi-dynamic-dropdown", "search_value"),
        State("my-multi-dynamic-dropdown", "value"),
    )
    def update_multi_options(search_value, value):
        if not search_value:
            raise PreventUpdate
        # Make sure that the set values are in the option list, else they will disappear
        # from the shown select list, but still part of the `value`.
        return [o for o in all_keys if search_value in o or o in (value or [])]

    @app.callback(
        Output("graph-1-tabs-dcc", "figure"),
        [
            Input("example-button", "n_clicks"),
            State("my-multi-dynamic-dropdown", "value"),
        ],
    )
    def on_button_click(n, selected_species):
        fig = get_fig0(selected_species)
        return fig

    app.layout = html.Div(
        [
            html.H1("UCLCHEM-viz DEMO"),
            dcc.Tabs(
                id="tabs-example-graph",
                value="tab-1-example-graph",
                children=[
                    dcc.Tab(label="Compare abundances", value="tab-1-example-graph"),
                    dcc.Tab(label="Compare more", value="tab-2-example-graph"),
                    dcc.Tab(label="Inspect one", value="tab-3-example-graph"),
                ],
            ),
            html.Div(id="tabs-content-example-graph"),
        ]
    )

    @app.callback(
        Output("tabs-content-example-graph", "children"),
        Input("tabs-example-graph", "value"),
    )
    def render_content(tab):
        if tab == "tab-1-example-graph":
            return html.Div(
                [
                    html.H3("Comparing abundances"),
                    dcc.Graph(figure=fig, id="graph-1-tabs-dcc"),
                    figdropdown,
                    button,
                ]
            )
        elif tab == "tab-2-example-graph":
            return html.Div(
                [
                    html.H3("Comparing abundances and rates"),
                    dcc.Graph(
                        id="graph-2-tabs-dcc",
                        figure=fig1,
                    ),
                ]
            )
        elif tab == "tab-3-example-graph":
            return html.Div(
                [
                    html.H3("In depth rate exploration"),
                    dcc.Graph(
                        id="graph-3-tabs-dcc",
                        figure=fig2,
                    ),
                ]
            )

    # app.layout = html.Div(
    #     children=[
    #         html.H1(children="UCLCHEM-viz"),
    #         dcc.Graph(id="Inspect reaction rates", figure=fig1),
    #         dcc.Graph(id="Inspect Abundances", figure=fig2),
    #     ]
    # )

    app.run_server(debug=True)
