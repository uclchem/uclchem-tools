import pandas as pd
import uclchem
from .rates import get_rates_of_change, rates_to_dfs

import yaml
import sys
import os

import warnings
from tables import NaturalNameWarning
import pandas as pd


if __name__ == "__main__":
    raise NotImplementedError("A wrapper for this function still needs to be written.")


def full_output_csv_to_hdf(
    csv_path: str,
    hdf_path: str,
    datakey: str = "",
    get_rates: bool = False,
    meta_data: dict = None,
):
    """Convert the full output of UCLCHEM into a HDF datastore.

    Args:
        csv_path (str): The path of the full output csv
        hdf_path (str): The path of the target hdf store
        datakey (str): the key for the particular dataframe. Defaults to "".
        get_rates (bool, optional): Whether to obtain the rates, dramatically reduces performance. Defaults to False.
    """
    # print(hdfpath)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=NaturalNameWarning)
        with pd.HDFStore(hdf_path, complevel=9, complib="zlib") as store:
            df = uclchem.analysis.read_output_file(csv_path)
            store.put(datakey + "/abundances", df)
            if meta_data:
                store.put(datakey, pd.DataFrame())
                store.get_storer(datakey).attrs.metadata = meta_data
            # Add reactions and species from current UCLCHEM install
            reactions = uclchem.utils.get_reaction_table()
            species = uclchem.utils.get_species_table()
            store.put(datakey + "/reactions", reactions)
            store.put(datakey + "/species", species)
            # POSTPROCESS UCLCHEM obtain the rates
            if get_rates:
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
                    store.put(f"{datakey}/rates/total_rates/{specie}", df_rates)
                    store.put(f"{datakey}/rates/production/{specie}", df_production)
                    store.put(f"{datakey}/rates/destruction/{specie}", df_destruction)
