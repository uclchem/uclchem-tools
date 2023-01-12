# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.0
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

from uclchem_tools import plot_rates

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
with open(
    "/home/vermarien/data2/uclchem-dev/v3.1.0/examples/test-output/phase2-full.yaml",
    "r",
) as fh:
    data_v3_1_p2 = yaml.safe_load(fh)
with open(
    "/home/vermarien/data2/uclchem-dev/v3.1.0-dev-h3tomolhydrogen/examples/test-output/phase2-full.yaml",
    "r",
) as fh:
    data_v3_2_p2 = yaml.safe_load(fh)


# %%
def analyze_rates(data, specie, axes, xlim):
    d1 = process_data(data, specie)
    plot_rates(**d1, fig=1, axes=axes, xlim=xlim)


fig, axes = plt.subplots(
    4,
    1,
    figsize=(10, 10),
    sharex=True,
    tight_layout=True,
    height_ratios=[1, 1, 1, 0.25],
)
xlim = [1e-6, 1e7]
analyze_rates(data_v3_1_p1, "CH3OH2+", axes=axes, xlim=xlim)
axes[0].set_title("v3.1.0")
fig.suptitle("Phase 1")


# %%
def plot_comparison(data1, data2, specie, xlim):
    fig, axes = plt.subplots(
        4,
        2,
        figsize=(20, 10),
        sharex=True,
        tight_layout=True,
        height_ratios=[1, 1, 3, 0.25],
    )
    d1 = process_data(data1, specie)
    d2 = process_data(data2, specie)
    # Make sure that the
    common_destruction_dict = {
        rf"{elem}": np.nanmean(d1["df_dest"][elem])
        for elem in set(d1["df_dest"].keys()).intersection(set(d2["df_dest"].keys()))
    }
    common_production_dict = {
        rf"{elem}": np.nanmean(d1["df_prod"][elem])
        for elem in set(d1["df_prod"].keys()).intersection(set(d2["df_prod"].keys()))
    }
    d1["df_dest"] = sort_reaction_df(
        d1["df_dest"], d1["df_dest"], common_destruction_dict
    )
    d2["df_dest"] = sort_reaction_df(
        d2["df_dest"], d1["df_dest"], common_destruction_dict
    )
    d1["df_prod"] = sort_reaction_df(
        d1["df_prod"], d1["df_prod"], common_production_dict
    )
    d2["df_prod"] = sort_reaction_df(
        d2["df_prod"], d1["df_prod"], common_production_dict
    )
    plot_rates(**d1, fig=1, axes=axes[:, 0], xlim=xlim)
    plot_rates(**d2, fig=1, axes=axes[:, 1], xlim=xlim)
    axes[0, 0].set_title("v3.1.0")
    axes[0, 1].set_title("v3.1.0-dev")
    return fig, axes


# %%
fig, axes = plot_comparison(data_v3_1_p1, data_v3_2_p1, "CH3OH", xlim=[2e6, 6e6])
[a.set_ylim(1e-28, 1e-10) for a in axes[0, :]]
fig.suptitle("Phase 1")

# %%
fig, axes = plot_comparison(data_v3_1_p1, data_v3_2_p1, "C+", xlim=[2e6, 6e6])
[a.set_ylim(1e-28, 1e-10) for a in axes[0, :]]
fig.suptitle("Phase 1")

# %%
fig, axes = plot_comparison(data_v3_1_p1, data_v3_2_p1, "HE+", xlim=[2e6, 6e6])
[a.set_ylim(1e-18, 1.3e-18) for a in axes[0, :]]
fig.suptitle("Phase 1")

# %%
fig, axes = plot_comparison(data_v3_1_p1, data_v3_2_p1, "CH3OH2+", xlim=[1e5, 1e7])
[a.set_ylim(1e-28, 1e-15) for a in axes[0, :]]
fig.suptitle("Phase 1")

# %%
fig, axes = plot_comparison(data_v3_1_p2, data_v3_2_p2, "CH3OH2+", xlim=[1e-6, 1e7])
fig.suptitle("Phase 2")

# %%

# %%

# %%
