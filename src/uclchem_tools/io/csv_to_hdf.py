import pandas as pd
import uclchem
from .rates import get_rates_of_change, rates_to_dfs

import yaml
import sys
import os

import warnings
from tables import NaturalNameWarning
import pandas as pd
import h5py
import numpy as np

from uclchem.makerates.reaction import reaction_types


if __name__ == "__main__":
    raise NotImplementedError("A wrapper for this function still needs to be written.")


class StorageBackend:
    """Meta class to specify how data is loaded, either from csv or from memory"""

    def __init__():
        pass


def to_h5py(fh, key, df):
    fh.create_dataset(
        f"/{key}",
        data=df.to_numpy(),
    )
    fh.create_dataset(f"/{key}_header", data=df.columns.values)


def full_output_csv_to_hdf(
    csv_path: str,
    hdf_path: str,
    datakey: str = "",
    get_rates: bool = False,
    meta_data: dict = None,
    assume_identical_networks: bool = False,
    storage_backend: str = "h5py",
):
    """Convert the full output of UCLCHEM into a HDF datastore.

    Args:
        csv_path (str): The path of the full output csv
        hdf_path (str): The path of the target hdf store
        datakey (str): the key for the particular dataframe. Defaults to "".
        get_rates (bool, optional): Whether to obtain the rates, dramatically reduces performance. Defaults to False.
    """
    abundances_header = None
    species_lookup = None
    if assume_identical_networks == False:
        raise NotImplementedError(
            "Writing and reading to different networks is not yet implemented."
        )
    if storage_backend == "h5py":
        with h5py.File(hdf_path, "a") as fh:
            df = uclchem.analysis.read_output_file(csv_path)
            # cast down to float32 since we lost accurary in custom ascii anyway.
            df = df.astype("float32")
            if not abundances_header:
                # Set the abundances header on first write of a grid.
                abundances_header = df.columns.values
            if (abundances_header == df.columns.values).all():
                to_h5py(fh, f"{datakey}/abundances", df)
            else:
                raise RuntimeError(
                    "I found different abundances columns from the first entry, stopping."
                )
            # Add reactions and species from current UCLCHEM install
            reactions = uclchem.utils.get_reaction_table()
            species = uclchem.utils.get_species_table()
            if assume_identical_networks:
                # TODO: refactor with species lookup table to get all integers instead of mixed data types.
                # SPECIE 0 is NAN
                if "index_species_lookup" in fh:
                    isl = fh["index_species_lookup"][:]
                    species_lookup = {k.decode("UTF-8"): int(v) for k, v in isl}
                else:
                    species_lookup = {
                        spec: i
                        for i, spec in enumerate(
                            ["NAN"] + list(species["NAME"]) + reaction_types
                        )
                    }
                    # Finally write the species to index lookup to the disk as an recarray:
                    # We need legacy "S" support to write to h5py
                    species_lookup_table = np.array(
                        [[k, v] for k, v in species_lookup.items()], dtype="S"
                    )
                    # species_lookup_table = np.stack((names_lookup, indices_lookup))

                    fh.create_dataset(
                        "/index_species_lookup", data=species_lookup_table
                    )
                # For all the headers of the reactants/products, replace them with integers.
                for reaction_header in reactions:
                    if reaction_header.startswith(
                        "Reactant"
                    ) or reaction_header.startswith("Product"):
                        reactions[
                            f"{reaction_header[:4].lower()}_index_{reaction_header[-1]}"
                        ] = (
                            reactions[reaction_header]
                            .apply(lambda x: species_lookup[str(x).upper()])
                            .astype("int32")
                        )
                # Identical for the names of the species in the index:
                species["name_index"] = (
                    species["NAME"]
                    .apply(lambda x: species_lookup[x.upper()])
                    .astype("int32")
                )
                # Drop the expensive text columns
                reactions = reactions.drop(
                    [
                        header
                        for header in reactions
                        if header.startswith("Reactant") or header.startswith("Product")
                    ],
                    axis=1,
                )
                species = species.drop(["NAME"], axis=1)
                # Sort the indices, so they move to the front:
                reactions = reactions[
                    sorted(reactions.columns, key=lambda x: "index" not in x)
                ]
                species = species[
                    sorted(species.columns, key=lambda x: "index" not in x)
                ]

                to_h5py(fh, f"{datakey}/reactions", reactions)
                to_h5py(fh, f"{datakey}/species", species)

            else:
                raise NotImplementedError(
                    "Not yet implemented for individual networks."
                )
        # POSTPROCESS UCLCHEM obtain the rates
        if get_rates:
            reactions = uclchem.utils.get_reaction_table()
            species = uclchem.utils.get_species_table()
            rates_dict = get_rates_of_change(df, species, reactions)
            # Lazy fix to parse both old and new versions species format:
            if "Name" in species:
                names = list(species["Name"])
            elif "NAME" in species:
                names = list(species["NAME"])
            for specie in names:
                df_rates, df_production, df_destruction = rates_to_dfs(
                    rates_dict, specie
                )
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=NaturalNameWarning)
                with pd.HDFStore(hdf_path) as store:
                    store.put(
                        f"{datakey}/rates/total_rates/{specie}",
                        df_rates,
                        index=False,
                    )
                    store.put(
                        f"{datakey}/rates/production/{specie}",
                        df_production,
                        index=False,
                    )
                    store.put(
                        f"{datakey}/rates/destruction/{specie}",
                        df_destruction,
                        index=False,
                    )
