import pandas as pd
import yaml
import numpy as np
import plotly.graph_objects as go
from tqdm import tqdm
import logging

from uclchem_tools.viz.plot import (
    plot_rates,
    plot_rates_comparison,
    plot_abundances_comparison,
    plot_abundances_comparison2,
    plot_rates_and_abundances_comparison,
)
from uclchem_tools.viz.process import process_data
from uclchem_tools.io.io import DataLoaderCSV, DataLoaderHDF

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


def get_unique_elements(data_dict):
    all_elements = []
    # for data_store in data_dict.values():
    for data_key in data_dict.keys():
        all_elements += data_dict[data_key]["species"]
    all_elements = list(np.unique(all_elements))
    for spec in all_elements:
        if spec.startswith("#") and spec.replace("#", "$") not in all_elements:
            all_elements.append(spec.replace("#", "$"))
        elif spec.startswith("@") and spec.replace("@", "$") not in all_elements:
            all_elements.append(spec.replace("@", "$"))

    for nonspecies in [
        "Time",
        "Density",
        "gasTemp",
        "av",
        "zeta",
        "point",
        "radfield",
    ]:
        if nonspecies in all_elements:
            all_elements.remove(nonspecies)
    return all_elements


# More dash things:


config = {"mode": "csv", "get_rates": False}  # or hdf


def load_csv(paths: list, matchstring: str = "*Full.dat"):
    # paths = ["comparison/v3.1/", "comparison/v3.2/"]
    data = [DataLoaderCSV(p, "*Full.dat", get_rates=True) for p in paths]
    return {k: v for k, v in zip(paths, data)}


def load_hdf(paths):
    if paths is not list:
        paths = [paths]
    data = [DataLoaderHDF(p) for p in paths]
    return {k: v for k, v in zip(paths, data)}


# PLOT THINGS


class LeftRightAbundancesPlot:
    """Compare abundances on the left and the right."""

    def __init__(datasets):
        pass


class TestComparisonPlot:
    """Compare the abundances in UCLCHEM to another on"""

    def __init__(self, datasets, app, id="testcompare"):
        self.datasets = datasets
        self.id = id
        self._app = app

    def get_fig(self, names_to_display):
        # names_to_display += ["Collapsing Cloud", "Hot Core", "Static Cloud"]
        fig = plot_abundances_comparison(
            self.datasets,
            names_to_display,
            list(self.datasets.keys())[:10],
            list(self.datasets.keys())[0],
            verbose=False,
            plot_temp=True,
        )
        return fig

    def get_view(self):
        fig = self.get_fig(
            [
                "H",
                "H2",
                "$H",
                "H2O",
                "$H2O",
                "CO",
                "$CO",
                "$CH3OH",
                "CH3OH",
            ]
        )
        dropdown, button = self.get_dash_options()
        return html.Div(
            [
                html.H3("Comparing abundances"),
                dcc.Graph(figure=fig + "-fig", id=self.id),
                dropdown,
                button,
            ]
        )

    def get_dash_options(
        self,
        default_species=[
            "H",
            "H2",
            "$H",
            "H2O",
            "$H2O",
            "CO",
            "$CO",
            "$CH3OH",
            "CH3OH",
        ],
    ):
        app = self._app
        all_keys = get_unique_elements(self.datasets)
        if any(map(lambda key: not key in all_keys, default_species)):
            logging.warning(
                "Not all default species are defined, defaulting to no species"
            )
            default_species = []
        dd = dcc.Dropdown(
            options=all_keys,
            value=default_species,
            id=self.id + "-dropdown",
            multi=True,
        )
        button = html.Div(
            [
                dbc.Button("Refresh", id=self.id + "-refresh-button", n_clicks=0),
                html.Span(
                    id=self.id + "example-output", style={"verticalAlign": "middle"}
                ),
            ]
        )

        @app.callback(
            Output(self.id + "-dropdown", "options"),
            Input(self.id + "-dropdown", "search_value"),
            State(self.id + "-dropdown", "value"),
        )
        def update_multi_options(self, search_value, value):
            if not search_value:
                raise PreventUpdate
            # Make sure that the set values are in the option list, else they will disappear
            # from the shown select list, but still part of the `value`.
            return [o for o in all_keys if search_value in o or o in (value or [])]

        @app.callback(
            Output(self.id + "-fig", "figure"),
            [
                Input(self.id + "-refresh-button", "n_clicks"),
                State(self.id + "-dropdown", "value"),
            ],
        )
        def on_button_click(self, n, selected_species):
            print(f"Got click number {n}")
            fig = self.get_fig(selected_species)
            return fig

        return dd, button


#
#
#
#


class LeftRightAbundancesAndRatesPlot:
    """Inspect both the rates and the adbundances between two datasets"""

    def __init__(self, datasets, app, id="lr-abundanceandrates"):
        print(datasets)
        self.datasets = datasets
        self.has_rates = (
            "rates" in datasets.keys()[0]
        )  # check if the first data element has rates present
        self._app = app
        self.id = id

    def get_view(self):
        # fig = self.get_fig(
        #     "H2O", "H2O", self.datasets.keys()[0], self.datasets.keys()[1]
        # )
        if self.has_rates:
            fig = self.get_fig(
                ["H2O"], "H2O", self.datasets.keys()[0], self.datasets.keys()[1]
            )
        else:
            fig = self.get_fig_no_rates(
                ["H2O"], "H2O", self.datasets.keys()[0], self.datasets.keys()[1]
            )
        # return fig

        options = self.get_dash_options()
        print(options)
        interactive_list = list(options.values())
        return html.Div(
            [
                html.H3("Comparing abundances and rates"),
                dcc.Graph(
                    id=self.id + "-fig",
                    figure=fig,
                ),
            ]
            + interactive_list
        )

    def get_dash_options(
        self,
        default_species=[
            "H",
            "H2",
            "$H",
            "H2O",
            "$H2O",
            "CO",
            "$CO",
            "$CH3OH",
            "CH3OH",
        ],
    ):
        app = self._app
        all_keys = get_unique_elements(self.datasets)
        if any(map(lambda key: not key in all_keys, default_species)):
            logging.warning(
                "Not all default species are defined, defaulting to no species"
            )
            default_species = []
        options_dict = {}
        options_dict["select_rates"] = dcc.Dropdown(
            options=all_keys,
            value="H2O",
            id=self.id + "-select-rates",
        )
        options_dict["select_species"] = dcc.Dropdown(
            options=all_keys,
            value=default_species,
            id=self.id + "-select-species",
            multi=True,
        )
        options_dict["select-data1"] = dcc.Dropdown(
            options=self.datasets.keys(),
            value=self.datasets.keys()[0],
            id=self.id + "-select-data1",
        )
        options_dict["select-data2"] = dcc.Dropdown(
            options=self.datasets.keys(),
            value=self.datasets.keys()[1],
            id=self.id + "-select-data2",
        )
        options_dict["refresh-button"] = html.Div(
            [
                dbc.Button("Refresh", id=self.id + "-refresh-button", n_clicks=0),
                html.Span(
                    id=self.id + "example-output", style={"verticalAlign": "right"}
                ),
            ]
        )

        @app.callback(
            Output(self.id + "-select-species", "options"),
            Input(self.id + "-select-species", "search_value"),
        )
        def update_options(search_value):
            if not search_value:
                raise PreventUpdate
            return [o for o in all_keys if search_value in o]

        @app.callback(
            Output(self.id + "-select-rates", "options"),
            Input(self.id + "-select-species", "search_value"),
            State(self.id + "-select-species", "value"),
        )
        def update_multi_options(search_value, value):
            if not search_value:
                raise PreventUpdate
            # Make sure that the set values are in the option list, else they will disappear
            # from the shown select list, but still part of the `value`.
            return [o for o in all_keys if search_value in o or o in (value or [])]

        @app.callback(
            Output(self.id + "-select-data1", "options"),
            Input(self.id + "-select-data1", "search_value"),
        )
        def update_options(search_value):
            if not search_value:
                raise PreventUpdate
            return [o for o in self.dataset.keys() if search_value in o]

        @app.callback(
            Output(self.id + "-select-data2", "options"),
            Input(self.id + "-select-data2", "search_value"),
        )
        def update_options(search_value):
            if not search_value:
                raise PreventUpdate
            return [o for o in self.dataset.keys() if search_value in o]

        @app.callback(
            Output(self.id + "-fig", "figure"),
            [
                Input(self.id + "-refresh-button", "n_clicks"),
                State(self.id + "-select-rates", "value"),
                State(self.id + "-select-species", "value"),
                State(self.id + "-select-data1", "value"),
                State(self.id + "-select-data2", "value"),
            ],
        )
        def on_button_click(n, selected_specie, abundance_species, d1, d2):
            print(f"Got click number {n}")
            if self.has_rates:
                fig = self.get_fig(abundance_species, selected_specie, d1, d2)
            else:
                fig = self.get_fig_no_rates(abundance_species, selected_specie, d1, d2)
            return fig

        return options_dict

    def get_fig(self, abundance_species, specie, data_key_1, data_key_2):
        fig = plot_rates_and_abundances_comparison(
            self.datasets[data_key_1],
            self.datasets[data_key_2],
            abundance_species,
            specie,
        )
        fig.update_layout(title_text=f"{data_key_1} vs {data_key_2}")
        fig.update_layout(
            height=1200,
        )
        return fig

    def get_fig_no_rates(self, abundance_species, specie, data_key_1, data_key_2):
        fig = plot_abundances_comparison2(
            [
                self.datasets[data_key_1]["abundances"],
                self.datasets[data_key_2]["abundances"],
            ],
            abundance_species,
        )
        fig.update_layout(title_text=f"{data_key_1} vs {data_key_2}")
        fig.update_layout(
            height=1200,
        )
        return fig


if __name__ == "__main__":

    datasets = list(
        load_hdf("/home/vermarien/data2/reduction-project/test.h5").values()
    )[0]
    # Dash things:
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.LUX],
        suppress_callback_exceptions=True,
    )

    tab_dict = {}
    if True:
        tab_dict["compare_abundances_and_rates"] = LeftRightAbundancesAndRatesPlot(
            datasets, app, id="compare_abundances_and_rates"
        )
    if True:
        tab_dict["uclchem_test_compare"] = TestComparisonPlot(
            datasets, app, id="uclchem_test_compare"
        )

    app.layout = html.Div(
        [
            html.H1("UCLCHEM-viz DEMO"),
            dcc.Tabs(
                id="tabs-example-graph",
                value=list(tab_dict)[0],  # "tab-1-example-graph",
                children=[dcc.Tab(label=key, value=key) for key in tab_dict],
            ),
            html.Div(id="tabs-content-example-graph"),
        ]
    )

    @app.callback(
        Output("tabs-content-example-graph", "children"),
        Input("tabs-example-graph", "value"),
    )
    def render_content(tab):
        return tab_dict[tab].get_view()
        # if tab == "tab-1-example-graph":
        #     return
        # elif tab == "tab-2-example-graph":
        #     return
        # elif tab == "tab-3-example-graph":
        #     return html.Div(
        #         [
        #             html.H3("In depth rate exploration: under construction"),
        #             html.Div(children=(html.Div(), html.Div()))
        #             # dcc.Graph(
        #             #     id="graph-3-tabs-dcc",
        #             #     figure=fig2,
        #             # ),
        #         ]
        #     )

    # app.layout = html.Div(
    #     children=[
    #         html.H1(children="UCLCHEM-viz"),
    #         dcc.Graph(id="Inspect reaction rates", figure=fig1),
    #         dcc.Graph(id="Inspect Abundances", figure=fig2),
    #     ]
    # )

    app.run_server(debug=True)
