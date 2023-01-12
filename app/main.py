from dash import Dash, html, dcc
import pandas as pd
import yaml
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from uclchem_tools import plot_rates, plot_rates_comparison
from uclchem_tools.viz.process import process_data


def analyze_rates(data, specie):
    d1 = process_data(data, specie)
    return plot_rates(**d1)


if __name__ == "__main__":
    # Data loading part:

    with open(
        "/home/vermarien/data2/uclchem-dev/v3.1.0/examples/test-output/phase1-full.yaml",
        "r",
    ) as fh:
        data_v3_1_p1 = yaml.safe_load(fh)
    with open(
        "/home/vermarien/data2/uclchem-dev/v3.1.0-dev-h3tomolhydrogen/examples/test-output/phase1-full.yaml",
        "r",
    ) as fh:
        data_v3_2_p1 = yaml.safe_load(fh)

    fig = plot_rates_comparison(data_v3_1_p1, data_v3_2_p1, "CH3OH")
    fig.update_layout(title_text="Phase 1")

    app = Dash(__name__)
    app.layout = html.Div(
        children=[
            html.H1(children="UCLCHEM-viz"),
            dcc.Graph(id="Inspect reaction rates", figure=fig),
        ]
    )

    app.run_server(debug=True)
