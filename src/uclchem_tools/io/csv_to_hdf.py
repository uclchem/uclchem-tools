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
from tqdm import tqdm
import pathlib
import logging
import glob

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


def read_h5py(fh, dataset_key):
    if isinstance(dataset_key, list):
        dataset_key = "/".join(dataset_key)
    data = fh[dataset_key]
    dataset_header_key = dataset_key + "_header"
    if dataset_header_key in fh:
        header = fh[dataset_header_key]
        return pd.DataFrame(data, columns=[col.decode("UTF-8") for col in header[:]])
    else:
        return pd.DataFrame(data)


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
                if not "reactions" in fh:
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
                            if header.startswith("Reactant")
                            or header.startswith("Product")
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

                    to_h5py(fh, f"/reactions", reactions)
                    to_h5py(fh, f"/species", species)

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


class GridConverter:
    """Convert a list of models run on a grid to a HDF dataset."""

    def __init__(
        self, hdf_path: pathlib.Path, model_df: pd.DataFrame, get_rates: bool = False
    ):
        if pathlib.Path(hdf_path).exists():
            raise RuntimeError("The store already exists, stoppping")
        if get_rates:
            logging.warning(
                "Obtaining all rates is very expensive, this will take a while."
            )
        # Save model_df with the model dataframe as a pandas object (inefficient, but we only store it once.)
        model_df["storage_id"] = self.get_storage_id(model_df)
        model_df.to_hdf(hdf_path, "model_df")
        for idx, row in tqdm(enumerate(model_df.iterrows()), total=len(model_df)):
            row = row[1]  # throw away the pandas index
            full_output_csv_to_hdf(
                row["outputFile"],
                hdf_path,
                row["storage_id"],
                get_rates=get_rates,
                assume_identical_networks=True,
            )

    def get_storage_id(self, model_df):
        return [f"grid_{i}" for i in range(len(model_df))]


class DataLoaderCSV:
    def __init__(self, csv_directory, match_statement="*Full.dat", get_rates=False):
        csv_files = [
            pathlib.Path(p) for p in glob.glob(csv_directory + match_statement)
        ]
        self.model_df = pd.DataFrame()
        self.model_df["FullOutput"] = csv_files
        self.model_df["storage_id"] = [p.stem for p in self.model_df["FullOutput"]]
        self.species = self.get_species()["Name"].to_list()
        self.reactions = self.get_reactions()
        self.csv_store = {}
        self.rates_store = {}
        for row in self.model_df.iterrows():
            row = row[1]
            row_id = row["storage_id"]
            if row_id in self.csv_store:
                raise RuntimeError(
                    "Found duplicate entries in the csv directory, make sure all names are unique"
                )
            fulloutput = uclchem.analysis.read_output_file(row["FullOutput"])
            self.csv_store[row_id] = fulloutput

            rates_dict = get_rates_of_change(fulloutput, self.species, self.reactions)
            self.rates_store[row_id] = {
                "total_rates": {},
                "production": {},
                "destruction": {},
            }
            for specie in self.species:
                total_rates, production, destruction = rates_to_dfs(rates_dict, specie)
                self.rates_store[row_id]["total_rates"][specie] = total_rates
                self.rates_store[row_id]["production"][specie] = production
                self.rates_store[row_id]["destruction"][specie] = destruction

    def keys(self):
        return list(self.csv_store.keys())

    def get_species(self):
        try:
            return uclchem.utils.get_species_table()
        except (NameError, AttributeError) as exc:
            raise exc("Cannot find UCLCHEM, so cannot obtain the species table")

    def get_reactions(self):
        try:
            return uclchem.utils.get_reaction_table()
        except (NameError, AttributeError) as exc:
            raise exc("Cannot find UCLCHEM, so cannot obtain the species table")

    def __getitem__(self, key) -> dict:
        return {
            **{
                "abundances": self.csv_store[key],
                "reactions": self.reactions,
                "species": self.species,
            },
            **self.rates_store[key],
        }


class DataLoaderHDF:
    def __init__(self, hdf_path):
        self.hdf_path = hdf_path
        self.h5file = h5py.File(hdf_path, mode="r")
        self.models_df = pd.read_hdf(hdf_path, "model_df")
        self.datasets = self.models_df["storage_id"].to_list()
        self._lookup_index_to_species = self.get_lookup_index_to_species()
        self.species_table = self._load_species_table()
        self.reaction_table = self._load_species_table()
        self.species = list(self.species_table["NAME"])
        self.reactions = None

    def get_lookup_index_to_species(self):
        lookup = self.h5file["index_species_lookup"]
        return {
            b: a.decode("UTF-8") for a, b in zip(lookup[:, 0], lookup[:, 1].astype(int))
        }

    def _load_species_table(self):
        species_table = read_h5py(self.h5file, "species")
        species_table["NAME"] = species_table["name_index"].apply(
            lambda r: self._lookup_index_to_species[r]
        )
        return species_table

    def _load_reactions_table(self):
        reactions_table = read_h5py(self.h5file, "reactions")
        for reaction in [r for r in reactions_table if "_index_" in r]:
            reactions_table[reaction.replace("_index_", " ").upper()] = reactions_table[
                reaction
            ].apply(lambda r: self._lookup_index_to_species[r])
        return reactions_table

    def get_species(self):
        return self.species_table["NAME"]

    def get_reactions(self):
        return self.reactions_table

    def keys(self):
        return self.get_datasets_keys()

    def get_datasets_keys(self):
        return self.datasets

    def __getitem__(self, key) -> dict:
        return {
            "abundances": read_h5py(self.h5file, key + "/abundances"),
            "reactions": self.reactions,
            "species": self.species,
            "total_rates": {
                spec: pd.read_hdf(self.hdf_path, f"{key}/rates/total_rates/{spec}")
                for spec in self.species
            },
            "production": {
                spec: pd.read_hdf(self.hdf_path, f"{key}/rates/production/{spec}")
                for spec in self.species
            },
            "destruction": {
                spec: pd.read_hdf(self.hdf_path, f"{key}/rates/destruction/{spec}")
                for spec in self.species
            },
        }
