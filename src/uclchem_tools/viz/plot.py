import matplotlib.pyplot as plt
from seaborn import color_palette
from cycler import cycler
from matplotlib.lines import Line2D

from .process import process_data, sort_reaction_df

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


def plot_rates(df, df_dest, df_prod, fig=None, axes=None, xlim=[None, None]):
    if not fig:
        fig, axes = plt.subplots(
            4,
            1,
            figsize=(10, 10),
            sharex=True,
            tight_layout=True,
            height_ratios=[1, 1, 1, 0.25],
        )
    ax = df.plot(ax=axes[0])

    ax.set(xscale="log", yscale="log")
    ax = df_prod.plot(ax=axes[1], legend=False)
    ax.set(ylim=[1e-3, 1.1], ylabel="Production (%)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    ax.set(xscale="log", yscale="log")
    ax = df_dest.plot(ax=axes[2], legend=False)
    ax.set(ylim=[1e-3, 1.1], ylabel="Destruction (%)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    ax.set(xscale="log", yscale="log")
    if xlim[0] or xlim[1]:
        ax.set(xlim=xlim)
    axes[-1].scatter(df.index, df.index != -1)
    [ax.grid(alpha=0.5) for ax in axes]
    return fig, axes
