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
import pandas as pd
from glob import glob
import uclchem
import matplotlib.pyplot as plt

from uclchem_tools import plot_abundances_comparison
import plotly.graph_objects as go


# %matplotlib notebook
from IPython.display import display, HTML

display(HTML("<style>.container { width:100% !important; }</style>"))


# %%
# %ls ../src/uclchem_tools/output_files

# %%
path = "../src/uclchem_tools/output_files/"
dirs = glob(path + "*.h5")
dirs = [
    "../src/uclchem_tools/output_files/v3.1.0.h5",
    "../src/uclchem_tools/output_files/v3.1.0-dev-h3tomolhydrogen.h5",
]
names = [dir_.split("/")[-1] for dir_ in dirs]
dfs = {
    name: {key: pd.read_hdf(dir_, key) for key in ["phase1", "phase2", "static"]}
    for name, dir_ in zip(names, dirs)
}
dfs.keys()

# %%
dfs["v3.1.0-dev-h3tomolhydrogen.h5"].keys()

# %%
speciesNames = [
    "H",
    "H2",
    "#H2",
    "$H",
    "H2O",
    "$H2O",
    # "CO",
    # "$CO",
    "$CH3OH",
    "CH3OH",
    "HE",
    "$HE",
]

# %%
speciesNames = [
    "HE",
    "@HE",
    "#HE",
]

# %%
speciesNames = [
    "H",
    "#H",
    "@H",
    "H2",
    "#H2",
    "@H2",
]

# %%
speciesNames = ["CO", "#CO", "@CO"]

# %%
from IPython.display import display
from ipywidgets import Checkbox, HBox, VBox, Box, Layout, Button, Output
import numpy as np

# %%
all_elements = [
    [df.columns.values for df in list(dfs.values())] for dfs in list(dfs.values())
]
unique_elements = []
for col1 in all_elements:
    for col2 in col1:
        for col3 in col2:
            if col3 not in unique_elements:
                if (
                    col3.startswith("#")
                    and col3.replace("#", "$") not in unique_elements
                ):
                    unique_elements.append(col3.replace("#", "$"))
                elif (
                    col3.startswith("@")
                    and col3.replace("@", "$") not in unique_elements
                ):
                    unique_elements.append(col3.replace("@", "$"))
                unique_elements.append(col3)

[
    unique_elements.remove(nonspecies)
    for nonspecies in ["Time", "Density", "gasTemp", "av", "zeta", "point", "radfield"]
]


# %%
unique_elements.sort(key=lambda x: x.replace("$", "").replace("@", "").replace("#", ""))

# %%
cols = 10
rows = len(unique_elements) // cols
try:
    boxes
except:
    boxes = [
        Checkbox(False, description=element, layout=Layout(max_width="175px"))
        for element in unique_elements
    ]
boxcontainer = []
for i in range(cols):
    rightbound = min(len(boxes), (i + 1) * rows)
    print(rightbound)
    boxcontainer.append(VBox(boxes[i * rows : rightbound]))
container = HBox(
    boxcontainer,
    layout=Layout(
        width="1920px",
        display="inline-flex",
    ),
)


# %%
render_button = Button(
    description="Make plots",
    disabled=False,
    button_style="",  # 'success', 'info', 'warning', 'danger' or ''
    tooltip="Click me",
    icon="check",
)


def on_change(a):
    global fig
    print("hello world")
    #    fig.data = []\
    species_we_want = [b.description for b in boxes if b.value] + [
        "phase1",
        "phase2",
        "static",
    ]
    species_to_plot = [
        True if name in ["H", "H2", "H2O", "phase1", "phase2", "static"] else False
        for name in names
    ]
    if len(species_to_plot) == 0:
        print("Did not select enough species.")
    else:
        # [ax.cla() for ax in axes.flatten()]
        #         fig  = plot_densities(
        #             dfs,
        #             s,
        #             list(dfs.keys()),
        #             list(dfs.keys())[0],
        #             verbose=False,
        #             fig=fig,
        #             plot_temp=True,
        #         )
        fig.plotly_restyle({"visible": species_to_plot})

        fig.show()


render_button.on_click(on_change)

# %%
dfs["v3.1.0.h5"].keys()

# %%
# display(container)
# display(render_button)
fig = plot_abundances_comparison(
    dfs,
    [b.description for b in boxes],
    list(dfs.keys()),
    list(dfs.keys())[0],
    verbose=False,
    plot_temp=True,
)
names = [d.name for d in fig.data]
species_to_plot = [
    True
    if name
    in ["H2+", "H2", "CO", "H3+", "Collapsing Cloud", "Hot Core", "Static Cloud"]
    else False
    for name in names
]
# visible = [b.description for b in boxes if b.value]
fig.plotly_restyle({"visible": species_to_plot})
f2 = go.FigureWidget(fig)
fig.update_layout(
    height=1200,
)
fig.show()

# %%
fig.layout["xaxis1"].matches = "x1"

# %%
fig.layout

# %%
fig.data

# %%

# %%

# %%

# %%

# %%

# %%
