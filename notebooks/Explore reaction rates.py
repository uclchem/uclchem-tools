# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import yaml
import matplotlib.pyplot as plt
import pandas as pd
from copy import deepcopy
import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots


from uclchem_tools import plot_rates, plot_rates_comparison
from uclchem_tools.viz.process import process_data

from IPython.display import display, HTML

display(HTML("<style>.container { width:100% !important; }</style>"))


# %%
# %%time
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
# with open("/home/vermarien/data2/uclchem-dev/v3.1.0/examples/test-output/phase2-full.yaml", "r") as fh:
#     data_v3_1_p2 = yaml.safe_load(fh)
# with open("/home/vermarien/data2/uclchem-dev/v3.1.0-dev-h3tomolhydrogen/examples/test-output/phase2-full.yaml", "r") as fh:
#     data_v3_2_p2 = yaml.safe_load(fh)

# %%
def analyze_rates(data, specie):
    d1 = process_data(data, specie)
    return plot_rates(**d1)


# fig, axes = plt.subplots(4,1, figsize = (10, 10), sharex=True, tight_layout=True, height_ratios=[1,1,1,0.25])
# fig = make_subplots(rows=3, cols=1, row_heights=[1, 1, 1], subplot_titles=("v3.1.0","Production", "Destruction", "Samples"), shared_xaxes=True, vertical_spacing = 0.03)
# xlim = [1e-6, 1e7]
fig = analyze_rates(data_v3_1_p1, "CH3OH")

fig.update_layout(
    height=1200,
    width=1000,
)
fig.update_layout(title_text="Phase 1")


# %%
fig = plot_rates_comparison(data_v3_1_p1, data_v3_2_p1, "CH3OH")
fig.update_layout(
    height=1200,
)
fig.update_layout(title_text="Phase 1")


# %%
fig = plot_rates_comparison(data_v3_1_p1, data_v3_2_p1, "C+")
fig.update_layout(
    height=1200,
)
fig.update_layout(title_text="Phase 1")


# %%
fig = plot_rates_comparison(data_v3_1_p1, data_v3_2_p1, "HE+")
fig.update_layout(
    height=1200,
)
fig.update_layout(title_text="Phase 1")


# %%
fig = plot_rates_comparison(data_v3_1_p1, data_v3_2_p1, "CH3OH2+")
fig.update_layout(
    height=1200,
)
fig.update_layout(title_text="Phase 1")


# %%
fig = plot_rates_comparison(data_v3_1_p2, data_v3_2_p2, "CH3OH2+")
fig.update_layout(
    height=1200,
)
fig.update_layout(title_text="Phase 2")


# %%

# %%

# %%
