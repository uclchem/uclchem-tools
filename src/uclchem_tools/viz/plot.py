import matplotlib.pyplot as plt
from seaborn import color_palette
from cycler import cycler
from matplotlib.lines import Line2D

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from .process import process_data, sort_by_intersection

custom_cycler = cycler(color=plt.get_cmap("tab10").colors) * cycler(
    linestyle=["solid", "dashed", "dotted", "dashdot"]
)
plt.rc("axes", prop_cycle=custom_cycler)


def plot_species(ax, df, species, **plot_kwargs):
    """Plot the abundance of a list of species through time directly onto an axis.

    Args:
        ax (pyplot.axis): An axis object to plot on
        df (pd.DataFrame): A dataframe created by `read_output_file`
        species (str): A list of species names to be plotted. If species name starts with "$" instead of # or @, plots the sum of surface and bulk abundances

    Returns:
        pyplot.axis: Modified input axis is returned
    """

    color_palette(n_colors=len(species))
    for specIndx, specName in enumerate(species):
        linestyle = "solid"
        if specName[0] == "$" and specName.replace("$", "#") in list(df.columns):
            abundances = df[specName.replace("$", "#")]
            linestyle = "dashdot"
            if specName.replace("$", "@") in df.columns:
                abundances = abundances + df[specName.replace("$", "@")]
        elif specName[0] == "#":
            linestyle = "dashed"
            abundances = df[specName]
        elif specName[0] == "@":
            linestyle = "dotted"
            abundances = df[specName]
        else:
            abundances = df[specName]
        if abundances.all() == 1e-30:
            addendum = " (np)"
        else:
            addendum = ""
        ax.plot(
            df["Time"],
            abundances,
            label=specName + addendum,
            lw=2,
            linestyle=linestyle,
            **plot_kwargs,
        )
    return ax


def plot_densities(
    dfs,
    species_to_plot,
    runs_to_include,
    reference_run=None,
    verbose=False,
    plot_temp=False,
    fig=None,
    axes=None,
):
    i = 0
    print(plot_temp)
    if not fig and not axes:
        height_ratios = [1] * len(runs_to_include)
        if plot_temp:
            height_ratios += [0.5]
        fig, axes = plt.subplots(
            len(runs_to_include) + 1 if plot_temp else 0,
            3,
            figsize=(24, 15),
            height_ratios=height_ratios,
            tight_layout=True,
            sharex=True,
        )
    #     axes = axes.flatten()
    model_names = {
        "phase1": "Collapsing Cloud",
        "phase2": "Hot Core",
        "static": "Static Cloud",
    }
    model_data = {}
    for idx_i, df_key in enumerate(runs_to_include):
        df = dfs[df_key]
        print(df.keys())
        for idx_j, model in enumerate(["phase1", "phase2", "static"]):
            axis = axes[idx_i, idx_j]
            axis.set_prop_cycle(cycler(color=plt.get_cmap("tab10").colors))

            # Handle species that are not there.
            for spec in species_to_plot:
                if spec not in list(df[model].columns):
                    if spec.startswith("$"):
                        if not spec.replace("$", "#") in df[model]:
                            df[model][spec.replace("$", "#")] = 1.0e-30
                        if not spec.replace("$", "@") in df[model]:
                            df[model][spec.replace("$", "@")] = 1.0e-30

            if verbose:
                print(
                    f"Testing element conservation for {df_key} in {model}: {uclchem.analysis.check_element_conservation(df[model])}"
                )
            # plot species and save to test.png, alternatively send dens instead of time.

            axis = plot_species(axis, df[model], species_to_plot)
            if reference_run and df_key != reference_run:
                axis.set_prop_cycle(None)
                axis.set_prop_cycle(cycler(color=plt.get_cmap("tab10").colors))
                axis = plot_species(
                    axis, dfs[reference_run][model], species_to_plot, alpha=0.5
                )
            # plot species returns the axis so we can further edit
            axis.set(xscale="log", ylim=(1e-24, 1), xlim=(1e-6, 6e6), yscale="log")

            if model == "phase1":
                axis.set(xlim=(2e6, 6e6))
            axis.set_title(model_names[model])
            i = i + 1

            if plot_temp:
                axes[-1, idx_j].plot(
                    df[model]["Time"], df[model]["gasTemp"], label=model
                )
                axes[-1, idx_j].set(ylabel="Temperature (K)")
        if reference_run and df_key != reference_run:
            axis.legend(
                [Line2D([0], [0], c="black"), Line2D([0], [0], alpha=0.5)],
                [df_key, reference_run],
                bbox_to_anchor=(1.05, 1),
                loc="upper left",
            )
    axes[0, -1].legend(
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )

    return fig, axes


def plot_rates_comparison(data1, data2, specie):
    fig = make_subplots(
        rows=3,
        cols=2,
        row_heights=[1, 1, 1],
        subplot_titles=["v3.1.0", "v3.1.0-dev"]
        + ["Production"] * 2
        + ["Destruction"] * 2,
        shared_xaxes=True,
        vertical_spacing=0.03,
    )
    d1 = process_data(data1, specie)
    d2 = process_data(data2, specie)
    # Make sure that the
    d1, d2 = sort_by_intersection(d1, d2, "df_dest")
    d1, d2 = sort_by_intersection(d1, d2, "df_prod")
    plot_rates(**d1, fig=fig, col=1, groupname="left")
    plot_rates(**d2, fig=fig, col=2, linedict=dict(dash="dash"), groupname="right")
    # axes[0, 0].set_title("v3.1.0")
    # axes[0, 1].set_title("v3.1.0-dev")
    return fig


def plot_rates(df, df_dest, df_prod, fig=None, col=1, linedict={}, groupname=None):
    if not fig:
        fig = make_subplots(
            rows=3,
            cols=1,
            row_heights=[1, 1, 1],
            subplot_titles=("v3.1.0", "Production", "Destruction", "Samples"),
            shared_xaxes=True,
            vertical_spacing=0.03,
        )
    print(groupname)
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
            ),
            col=col,
            row=1,
        )
        for term in df
    ]

    # Plot the contribution of each reaction to the production ...
    for prod_term in df_prod:
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
            ),
            col=col,
            row=2,
        )
    # ... and the destruction despectively.
    for dest_term in df_dest:
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
            ),
            col=col,
            row=3,
        )

    fig.update_layout(legend=dict(groupclick="toggleitem"), hovermode="x unified")
    fig.update_xaxes(type="log", tickformat="~e")
    fig.update_yaxes(type="log")
    # Scientific units for the rates, percentages for the contribution of the reactions.
    [
        fig.layout[f"yaxis{i+1 if i>0 else ''}"].update(tickformat=style)
        for i, style in enumerate(["~e", "~%", "~%"])
    ]
    return fig
