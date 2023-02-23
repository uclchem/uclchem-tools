from tqdm import tqdm
import numpy as np
from copy import deepcopy
import pandas as pd
import uclchem
from joblib import Parallel, delayed

from uclchem.uclchemwrap import uclchemwrap


def key_reactions_to_dict(
    time, total_production, total_destruction, key_reactions, key_changes
):
    """Prints key reactions to file

    Args:
        time (float): Simulation time at which analysis is performed
        total_production (float): Total positive rate of change
        total_destruction (float): Total negative rate of change
        key_reactions (list): A list of all reactions that contribute to the total rate of change
        key_changes (list): A list of rates of change contributing to total
    """
    return {
        "time": float(time),
        "total_production": float(total_production),
        "total_destruction": float(total_destruction),
        "key_production_reactions": {
            str(reac): float(key_changes[k] / total_production)
            for k, reac in enumerate(key_reactions)
            if key_changes[k] > 0
        },
        "key_destruction_reactions": {
            str(reac): float(key_changes[k] / total_destruction)
            for k, reac in enumerate(key_reactions)
            if key_changes[k] < 0
        },
    }


def _get_rate_of_chance(result_df, reactions, species, species_name, rate_threshold):
    fortran_reac_indxs = [
        i + 1 for i, reaction in enumerate(reactions) if species_name in reaction
    ]
    reac_indxs = [i for i, reaction in enumerate(reactions) if species_name in reaction]
    species_index = species.index(species_name) + 1  # fortran index of species
    data = {}
    if len(reac_indxs) <= 500 and species_name not in ["BULK", "SURFACE"]:
        failed_species = []
        for i, row in result_df.iterrows():
            # recreate the parameter dictionary needed to get accurate rates
            param_dict = uclchem.analysis._param_dict_from_output(row)
            # get the rate of all reactions from UCLCHEM along with a few other necessary values
            (
                rates,
                transfer,
                swap,
                bulk_layers,
            ) = uclchem.analysis._get_species_rates(
                param_dict, row[species], species_index, fortran_reac_indxs
            )

            # convert reaction rates to total rates of change, this needs manually updating when you add new reaction types!
            change_reacs, changes = uclchem.analysis._get_rates_of_change(
                rates,
                reactions[reac_indxs],
                species,
                species_name,
                row,
                swap,
                bulk_layers,
            )

            change_reacs = uclchem.analysis._format_reactions(change_reacs)

            # This whole block adds the transfer of material from surface to bulk as surface grows (or vice versa)
            # it's not a reaction in the network so won't get picked up any other way. We manually add it.
            if species_name[0] == "@":
                if transfer >= 0:
                    change_reacs.append(
                        f"#{species_name[1:]} + SURFACE_TRANSFER -> {species_name}"
                    )
                else:
                    change_reacs.append(
                        f"{species_name} + SURFACE_TRANSFER -> #{species_name[1:]}"
                    )
                changes = np.append(changes, transfer)
            elif species_name[0] == "#":
                if transfer >= 0:
                    change_reacs.append(
                        f"@{species_name[1:]} + SURFACE_TRANSFER -> {species_name}"
                    )
                else:
                    change_reacs.append(
                        f"{species_name} + SURFACE_TRANSFER -> @{species_name[1:]}"
                    )
                changes = np.append(changes, transfer)
            # Then we remove the reactions that are not important enough to be printed by finding
            # which of the top reactions we need to reach rate_threshold*total_rate
            (
                total_formation,
                total_destruct,
                key_reactions,
                key_changes,
            ) = uclchem.analysis._remove_slow_reactions(
                changes, change_reacs, rate_threshold=rate_threshold
            )
            data[float(row["Time"])] = key_reactions_to_dict(
                row["Time"],
                total_formation,
                total_destruct,
                key_reactions,
                key_changes,
            )
        # except:
        #     if not species_name in failed_species:
        #         print(f"for {species_name} something went wrong for step {i}.")
        #         failed_species.append(species_name)
        print(f"Just analyzed {species_name}")
    else:
        print(f"{species_name} contains more than 500 species, we are skipping it.")
    return data


def get_rates_of_change(result_df, species, reactions, rate_threshold=0.99):
    """A function which loops over every time step in an output file and finds the rate of change of a species at that time due to each of the reactions it is involved in.
    From this, the most important reactions are identified and printed to file. This can be used to understand the chemical reason behind a species' behaviour.

    Args:
        result_file (str): The path to the file containing the UCLCHEM output
        rate_threshold (float,optional): Analysis output will contain the only the most efficient reactions that are responsible for rate_threshold of the total production and destruction rate. Defaults to 0.99.
    """
    if "Name" in species:
        species = list(species["Name"])
    elif "NAME" in species:
        species = list(species["NAME"])
    reactions = reactions[
        [
            "Reactant 1",
            "Reactant 2",
            "Reactant 3",
            "Product 1",
            "Product 2",
            "Product 3",
            "Product 4",
        ]
    ].to_numpy()
    # all_analyses = {}
    print(f"Found {len(species)} species, brace yourselves.")
    # Get all the reaction rates with parallel worker:
    rates = Parallel(n_jobs=100)(
        delayed(_get_rate_of_chance)(
            result_df, reactions, species, species_name, rate_threshold
        )
        for species_name in species
    )
    return {k: v for k, v in zip(species, rates)}

    # new_name = results_file.replace(".dat", ".yaml")
    # with open(new_name, "w") as outfile:
    #     yaml.dump(all_analyses, outfile)


def rates_to_dfs(data, specie):
    if (not specie in data) or (len(data[specie]) == 0):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    # print(data.keys(), specie)
    # print(data[specie])
    key_destruction_reactions = {}
    key_production_reactions = {}
    data_copy = deepcopy(data[specie])
    for time_key in data_copy:
        key_destruction_reactions[time_key] = data_copy[time_key].pop(
            "key_destruction_reactions"
        )
        key_production_reactions[time_key] = data_copy[time_key].pop(
            "key_production_reactions"
        )
    df = pd.DataFrame.from_dict(data_copy).transpose()
    df.set_index("time", inplace=True)
    df.index.set_names("Time", inplace=True)
    df["total_destruction"] *= -1.0  # make destruction positive so we can plot it.
    df_dest = pd.DataFrame.from_dict(key_destruction_reactions).transpose()
    df_dest.index.set_names(["Time"], inplace=True)
    df_prod = pd.DataFrame.from_dict(key_production_reactions).transpose()
    df_prod.index.set_names(["Time"], inplace=True)
    return df, df_prod, df_dest


### NEW STUFF


def get_abundances_derivative(abundances_df, param_dict):
    """This function takes the abundance and environment parameters at each timestep,
    then reinitializes the simulation with the physics parameters to obtain the deriative.

    Args:
        abundances (_type_): _description_
        param_dict (_type_): _description_

    Returns:
        _type_: _description_
    """
    if "finalTime" in param_dict:
        # pop these 3 as they are not supported?
        param_dict.pop("finalTime")
        param_dict.pop("baseAv")
        param_dict.pop("freezeFactor")
    derivatives_df = abundances_df.copy()
    # for idx, row in tqdm(abundances_df.iterrows(), total=len(abundances_df)):
    for idx, row in abundances_df.iterrows():
        input_abund = np.zeros(500)
        param_dict["initialdens"] = row["Density"]
        param_dict["initialtemp"] = row["gasTemp"]
        param_dict["zeta"] = row["zeta"]
        param_dict["radfield"] = row["radfield"]
        row_ = row.iloc[6:-1]
        input_abund[: len(row_)] = row_
        rates = uclchemwrap.get_odes(param_dict, input_abund)
        derivatives_df.iloc[idx, 6:-1] = rates[: len(row_)]
    return derivatives_df
