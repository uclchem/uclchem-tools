import matplotlib.pyplot as plt
from seaborn import color_palette
from cycler import cycler
from matplotlib.lines import Line2D

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np


def get_color(idx):
    colors = px.colors.qualitative.D3
    return colors[idx % len(colors)]


from .process import process_data, sort_by_intersection

custom_cycler = cycler(color=plt.get_cmap("tab10").colors) * cycler(
    linestyle=["solid", "dashed", "dotted", "dashdot"]
)
plt.rc("axes", prop_cycle=custom_cycler)

#            ____  _    _ _   _ _____          _   _  _____ ______  _____
#      /\   |  _ \| |  | | \ | |  __ \   /\   | \ | |/ ____|  ____|/ ____|
#     /  \  | |_) | |  | |  \| | |  | | /  \  |  \| | |    | |__  | (___
#    / /\ \ |  _ <| |  | | . ` | |  | |/ /\ \ | . ` | |    |  __|  \___ \
#   / ____ \| |_) | |__| | |\  | |__| / ____ \| |\  | |____| |____ ____) |
#  /_/    \_\____/ \____/|_| \_|_____/_/    \_\_| \_|\_____|______|_____/


def _plot_abundance(fig, df, species, col=1, row=1, grouptitle=None, **plot_kwargs):
    """Plot the abundance of a list of species through time directly onto an axis.

    Args:
        ax (pyplot.axis): An axis object to plot on
        df (pd.DataFrame): A dataframe created by `read_output_file`
        species (str): A list of species names to be plotted. If species name starts with "$" instead of # or @, plots the sum of surface and bulk abundances

    Returns:
        pyplot.axis: Modified input axis is returned
    """

    # color_palette(n_colors=len(species))
    for specIndx, specName in enumerate(species):
        linestyle = "solid"
        if specName in df:
            if specName[0] == "#":
                linestyle = "dash"
            elif specName[0] == "@":
                linestyle = "dot"
            abundances = df[specName]
        else:
            if specName.startswith("$") and specName.replace("$", "#") in list(
                df.columns
            ):
                abundances = df[specName.replace("$", "#")]
                linestyle = "dashdot"
                if specName.replace("$", "@") in df.columns:
                    abundances = abundances + df[specName.replace("$", "@")]
            else:
                abundances = np.full(df.index.shape, np.nan)

        if abundances.all() == 1e-30:
            addendum = " (np)"
        else:
            addendum = ""
        fig.add_trace(
            go.Scatter(
                x=df["Time"],
                y=abundances,
                name=specName + addendum,
                legendgroup=f"{row},{col}",
                legendgrouptitle_text=grouptitle,
                marker_color=get_color(specIndx),
                hovertemplate="%{y:.2e}",
                line=dict(dash=linestyle),
            ),
            col=col,
            row=row,
        )
    return fig


def plot_abundances_comparison(
    dfs,
    species_to_plot,
    runs_to_include,
    reference_run=None,
    verbose=False,
    plot_temp=False,
    fig=None,
):
    print(species_to_plot)
    model_names = {
        "phase1Full": "Collapsing Cloud",
        "phase2Full": "Hot Core",
        "staticFull": "Static Cloud",
    }
    height = len(runs_to_include) + 1 if plot_temp else 0
    width = len(model_names)

    if not fig:
        fig = make_subplots(
            rows=height,
            cols=width,
            subplot_titles=list(model_names.values()),
            shared_xaxes="columns",
            vertical_spacing=0.03,
        )

    for idx_i, df_key in enumerate(runs_to_include):
        df = dfs[df_key]
        for idx_j, model in enumerate(model_names):

            # Handle creating a total ice abundance (bulk + surface).
            for spec in species_to_plot:
                if spec not in list(df[model]["abundances"].columns):
                    if spec.startswith("$"):
                        if not spec.replace("$", "#") in df[model]["abundances"]:
                            df[model]["abundances"][spec.replace("$", "#")] = 1.0e-30
                        if not spec.replace("$", "@") in df[model]["abundances"]:
                            df[model]["abundances"][spec.replace("$", "@")] = 1.0e-30

            if verbose:
                print(
                    f"Testing element conservation for {df_key} in {model}: {uclchem.analysis.check_element_conservation(df[model]['abundances'])}"
                )
            # Plot the lines
            fig = _plot_abundance(
                fig,
                df[model]["abundances"],
                species_to_plot,
                row=idx_i + 1,
                col=idx_j + 1,
                grouptitle=f"{df_key}: {model}",
            )
            # If we are in lower rows, fix the y-axis so they are identical for all rows but temperature
            if idx_j > 0:
                fig.layout[
                    f"yaxis{idx_i*len(runs_to_include)+idx_j+1}"
                ].matches = f"y{idx_i+1}"
        # Only plot the temperature once at the end

    for idx_j, model in enumerate(model_names):
        if plot_temp:
            fig.add_trace(
                go.Scatter(
                    x=df[model]["abundances"]["Time"].values,
                    y=df[model]["abundances"]["gasTemp"].values,
                    legendgroup="Temperatures",
                    legendgrouptitle_text="Temperatures",
                    name=model_names[model],
                ),
                col=idx_j + 1,
                row=width,
            )
    fig.update_layout(legend=dict(groupclick="toggleitem"), hovermode="x unified")
    fig.update_xaxes(type="log", exponentformat="power")
    # Add time labels
    xaxis_labels = ["Time (yr)"] * len(model_names)
    [
        fig.update_xaxes(title_text=label, row=height, col=i + 1)
        for i, label in enumerate(xaxis_labels)
    ]
    yaxis_labels = ["Abundances (-)"] * len(runs_to_include) + ["Temperature (K)"]
    [
        fig.update_yaxes(title_text=label, row=i + 1, col=1)
        for i, label in enumerate(yaxis_labels)
    ]
    # Add titles:
    # [
    #     fig.update_title(title=model_names[name], row=1, col=i + 1)
    #     for i, name in enumerate(model_names)
    # ]
    fig.update_yaxes(type="log", exponentformat="power")
    return fig


def plot_abundances_comparison2(
    dfs,
    species_to_plot,
    reference_run=None,
    verbose=False,
    plot_temp=False,
    fig=None,
):
    model_names = {
        "phase1Full": "Collapsing Cloud",
        "phase2Full": "Hot Core",
        "staticFull": "Static Cloud",
    }
    height = len(dfs) + 1 if plot_temp else 0
    width = 1

    if not fig:
        fig = make_subplots(
            rows=height,
            cols=width,
            # subplot_titles=("v3.1.0", "Production", "Destruction", "Samples"),
            shared_xaxes="all",
            vertical_spacing=0.03,
        )

    for idx_i, df in enumerate(dfs):
        # Handle creating a total ice abundance (bulk + surface).
        for spec in species_to_plot:
            if spec not in list(df.columns):
                if spec.startswith("$"):
                    if not spec.replace("$", "#") in df:
                        df[spec.replace("$", "#")] = 1.0e-30
                    if not spec.replace("$", "@") in df:
                        df[spec.replace("$", "@")] = 1.0e-30

        if verbose:
            # print(
            #     f"Testing element conservation for {df_key} in {model}: {uclchem.analysis.check_element_conservation(df)}"
            # )
            pass
        # Plot the lines
        fig = _plot_abundance(
            fig,
            df,
            species_to_plot,
            row=idx_i + 1,
            col=1,
            grouptitle=f"{idx_i}",
        )
        # If we are in lower rows, fix the y-axis so they are identical for all rows but temperature
        # if idx_i > 0:
        #     fig.layout[
        #         f"yaxis{idx_i*len(runs_to_include)+idx_j+1}"
        #     ].matches = f"y{idx_j+1}"
    # Only plot the temperature once at the end

    if plot_temp:
        fig.add_trace(
            go.Scatter(
                x=df["Time"].values,
                y=df["gasTemp"].values,
                legendgroup="Temperatures",
                legendgrouptitle_text="Temperatures",
                name="Temperature",
            ),
            col=1,
            row=3,
        )
    fig.update_layout(legend=dict(groupclick="toggleitem"), hovermode="x unified")
    fig.update_xaxes(type="log", exponentformat="power")
    # Add time labels
    xaxis_labels = ["Time (yr)"] * len(model_names)
    [
        fig.update_xaxes(title_text=label, row=height, col=i + 1)
        for i, label in enumerate(xaxis_labels)
    ]
    yaxis_labels = ["Abundances (-)"] * 2 + ["Temperature (K)"]
    [
        fig.update_yaxes(title_text=label, row=i + 1, col=1)
        for i, label in enumerate(yaxis_labels)
    ]
    # Add titles:
    [
        fig.update_yaxes(title=model_names[name], row=1, col=i + 1)
        for i, name in enumerate(model_names)
    ]
    fig.update_yaxes(type="log", exponentformat="power")
    return fig


#   _____         _______ ______  _____
#  |  __ \     /\|__   __|  ____|/ ____|
#  | |__) |   /  \  | |  | |__  | (___
#  |  _  /   / /\ \ | |  |  __|  \___ \
#  | | \ \  / ____ \| |  | |____ ____) |
#  |_|  \_\/_/    \_\_|  |______|_____/
#


def plot_rates_comparison(data1, data2, specie):
    fig = make_subplots(
        rows=3,
        cols=2,
        row_heights=[1, 1, 1],
        subplot_titles=["v3.1.0", "v3.1.0-dev"]
        + ["Production"] * 2
        + ["Destruction"] * 2,
        shared_xaxes="all",
        vertical_spacing=0.03,
    )
    d1 = process_data(data1, specie)
    d2 = process_data(data2, specie)
    # Make sure that the
    d1, d2 = sort_by_intersection(d1, d2, "df_dest")
    d1, d2 = sort_by_intersection(d1, d2, "df_prod")
    plot_rates(**d1, fig=fig, col=1, groupname="left")
    plot_rates(**d2, fig=fig, col=2, linedict=dict(dash="dash"), groupname="right")
    fig.layout["xaxis2"].matches = "x1"
    # Fix the formatting of the numbers on the axes
    [
        fig.layout[f"yaxis{i+1 if i>0 else ''}"].update(tickformat=style)
        for i, style in enumerate(["~e", "~e", "~%", "~%", "~%", "~%"])
    ]
    # Add time labels
    xaxis_labels = ["Time (yr)"] * 2
    [
        fig.update_xaxes(title_text=label, row=3, col=i + 1)
        for i, label in enumerate(xaxis_labels)
    ]
    yaxis_labels = [r"$\mathrm{Rates}\;(s^{-1})$", "Production", "Destruction"]
    [
        fig.update_yaxes(title_text=label, row=i + 1, col=1)
        for i, label in enumerate(yaxis_labels)
    ]
    return fig


def plot_rates(df, df_dest, df_prod, fig=None, col=1, linedict={}, groupname=None):
    if not fig:
        fig = make_subplots(
            rows=3,
            cols=1,
            row_heights=[1, 1, 1],
            subplot_titles=("v3.1.0", "Production", "Destruction", "Samples"),
            shared_xaxes="all",
            vertical_spacing=0.03,
        )
    # Plot the rates at which the species are produced and destroyed
    [
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[term],
                name=term,
                legendgroup="1",
                legendgrouptitle_text="Rates",
                mode="lines+markers",
                hoverlabel=dict(namelength=-1),
            ),
            col=col,
            row=1,
        )
        for term in df
    ]

    # Plot the contribution of each reaction to the production ...
    for idx, prod_term in enumerate(df_prod):
        print(f"Production reactions {groupname}")
        #
        fig.add_trace(
            go.Scatter(
                x=df_prod.index,
                y=df_prod[prod_term],
                name=prod_term,
                line=linedict,
                legendgrouptitle_text=f"Production reactions {groupname if groupname else ''}",
                legendgroup="2" + str(groupname),
                mode="lines+markers",
                hovertemplate="%{y:.2e}",
                hoverlabel=dict(namelength=-1),
                marker_color=get_color(idx),
            ),
            col=col,
            row=2,
        )
    # ... and the destruction despectively.
    for idx, dest_term in enumerate(df_dest):
        # f"Destruction reactions {groupname}"
        fig.add_trace(
            go.Scatter(
                x=df_dest.index,
                y=df_dest[dest_term],
                name=dest_term,
                line=linedict,
                legendgrouptitle_text=f"Destruction reactions {groupname if groupname else ''}",
                legendgroup="3" + str(groupname),
                mode="lines+markers",
                hovertemplate="%{y:.2e}",
                hoverlabel=dict(namelength=-1),
                marker_color=get_color(idx),
            ),
            col=col,
            row=3,
        )

    fig.update_layout(legend=dict(groupclick="toggleitem"), hovermode="x unified")
    fig.update_xaxes(type="log", tickformat="~e")
    # fig.update_xaxes(title_text="Time (yr)", row=3, col=1)
    fig.update_yaxes(type="log")
    # Scientific units for the rates, percentages for the contribution of the reactions.
    [
        fig.layout[f"yaxis{i+1 if i>0 else ''}"].update(tickformat=style)
        for i, style in enumerate(["~e", "~%", "~%"])
    ]
    yaxis_labels = [r"$\mathrm{Rates}\;(s^{-1})$", "Production", "Destruction"]
    [
        fig.update_yaxes(title_text=label, row=i + 1, col=1)
        for i, label in enumerate(yaxis_labels)
    ]
    return fig


def plot_rates_and_abundances_comparison(
    data1, data2, abundance_species, rates_species
):
    print(f"Abundances: {abundance_species}, rates: {rates_species}")
    fig = make_subplots(
        rows=4,
        cols=2,
        row_heights=[1, 1, 1, 1],
        subplot_titles=["v3.1.0", "v3.1.0-dev"]
        + ["Production"] * 2
        + ["Destruction"] * 2
        + ["Abundances"] * 2,
        shared_xaxes="all",
        vertical_spacing=0.03,
        shared_yaxes="rows",
    )
    d1 = process_data(data1["rates"], rates_species)
    d2 = process_data(data2["rates"], rates_species)
    # Make sure that the
    d1, d2 = sort_by_intersection(d1, d2, "df_dest")
    d1, d2 = sort_by_intersection(d1, d2, "df_prod")
    plot_rates(**d1, fig=fig, col=1, groupname="left")
    plot_rates(**d2, fig=fig, col=2, groupname="right")

    _plot_abundance(
        fig, data1["abundances"], abundance_species, col=1, row=4, grouptitle="left"
    )
    _plot_abundance(
        fig, data2["abundances"], abundance_species, col=2, row=4, grouptitle="right"
    )
    fig.layout["xaxis2"].matches = "x1"
    # Fix the formatting of the numbers on the axes
    [
        fig.layout[f"yaxis{i+1 if i>0 else ''}"].update(tickformat=style)
        for i, style in enumerate(["~e", "~e", "~%", "~%", "~%", "~%", "~e", "~e"])
    ]
    # Add time labels
    xaxis_labels = ["Time (yr)"] * 2
    [
        fig.update_xaxes(title_text=label, row=4, col=i + 1)
        for i, label in enumerate(xaxis_labels)
    ]
    yaxis_labels = [
        r"$\mathrm{Rates}\;(s^{-1})$",
        "Production",
        "Destruction",
        "Abundances",
    ]
    [
        fig.update_yaxes(title_text=label, row=i + 1, col=1)
        for i, label in enumerate(yaxis_labels)
    ]
    return fig
