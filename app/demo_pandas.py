from dash import Dash, dash_table
import pandas as pd

from uclchem_tools.io.io import DataLoaderHDF

# df = pd.read_csv("http://raw.githubusercontent.com/plotly/datasets/master/solar.csv")
def load_hdf(paths):
    if paths is not list:
        paths = [paths]
    data = [DataLoaderHDF(p) for p in paths]
    return {k: v for k, v in zip(paths, data)}


datasets = list(load_hdf("/home/vermarien/data2/reduction-project/test.h5").values())[0]


app = Dash(__name__)

app.layout = dash_table.DataTable(
    datasets.models_df.to_dict("records"),
    [{"name": i, "id": i} for i in datasets.models_df.columns],
)

if __name__ == "__main__":

    app.run_server(debug=True)
