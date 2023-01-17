from dash import Dash, html, dcc
import pandas as pd
import yaml
import numpy as np
import plotly.graph_objects as go
from tqdm import tqdm
from plotly.subplots import make_subplots
from uclchem_tools import plot_rates, plot_rates_comparison, plot_abundances_comparison2
from uclchem_tools.viz.process import process_data


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
        print("Being lazy", key, type(self.values_dict[key]))
        print(self.values_dict.keys())
        if not isinstance(self.values_dict[key], pd.DataFrame):
            with pd.HDFStore(self.h5root, complevel=9, complib="zlib") as store:
                self.values_dict[key] = store.get(f"{self.walker}/{key}")
        print("After being non-lazy", key, type(self.values_dict[key]))
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


if __name__ == "__main__":
    # Data loading part:
    paths = ["comparison/v3.1/test-store.h5", "comparison/v3.2/test-store.h5"]
    data = [load_data(path)["phase1Full"] for path in paths]
    # with open(
    #     "/home/vermarien/data2/uclchem-dev/v3.1.0/examples/test-output/phase1-full.yaml",
    #     "r",
    # ) as fh:
    #     data_v3_1_p1 = yaml.safe_load(fh)
    # with open(
    #     "/home/vermarien/data2/uclchem-dev/v3.1.0-dev-h3tomolhydrogen/examples/test-output/phase1-full.yaml",
    #     "r",
    # ) as fh:
    #     data_v3_2_p1 = yaml.safe_load(fh)

    print(data[0])
    fig1 = plot_rates_comparison(data[0]["rates"], data[1]["rates"], "CH3OH")
    fig1.update_layout(title_text="Phase 1")

    fig2 = plot_abundances_comparison2(
        [data[0]["abundances"], data[1]["abundances"]],
        ["CH3OH2+", "$CH3OH", "CH3OH"],
        plot_temp=True,
    )
    fig2.update_layout(title_text="Phase 1")

    app = Dash(__name__)
    app.layout = html.Div(
        children=[
            html.H1(children="UCLCHEM-viz"),
            dcc.Graph(id="Inspect reaction rates", figure=fig1),
            dcc.Graph(id="Inspect Abundances", figure=fig2),
        ]
    )

    app.run_server(debug=True)
