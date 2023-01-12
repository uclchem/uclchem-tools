import pandas as pd
import numpy as np
from cycler import cycler
from copy import deepcopy


def process_data(data, specie):
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
    df["total_destruction"] *= -1  # make destruction positive so we can plot it.
    df_dest = pd.DataFrame.from_dict(key_destruction_reactions).transpose()
    df_dest.index.set_names(["Time"], inplace=True)
    df_prod = pd.DataFrame.from_dict(key_production_reactions).transpose()
    df_prod.index.set_names(["Time"], inplace=True)
    df_dest.columns = [
        name.replace(f"{specie} ", r" $\bf{" + str(specie) + "}$ ")
        for name in df_dest.columns
    ]
    df_prod.columns = [
        name.replace(f"{specie} ", r" $\bf{" + str(specie) + "}$ ")
        for name in df_prod.columns
    ]

    return {"df": df, "df_dest": df_dest, "df_prod": df_prod}


def sort_reaction_df(df, reference_df, common_dict):
    # write to dict because sorting indexes is weird
    df_dict = df.to_dict()
    ref_df_dict = reference_df.to_dict()
    # Sort the keys first by whether they are matching, then by the average values of the reference dictionary
    # If it is not matching, just sort by its own average value in descending order
    df_dict = dict(
        sorted(
            df_dict.items(),
            key=lambda kv: (
                int(kv[0] not in common_dict.keys()),
                -np.nanmean(list(ref_df_dict[kv[0]].values()))
                if kv[0] in common_dict.keys()
                else -np.nanmean(list(kv[1].values())),
            ),
        )
    )
    # print("\n", "\n".join([f"{r}\t,{int(r not in common_dict)},\t{np.nanmean(df[r])}" for r in temp_df.columns]), "\n")
    return pd.DataFrame.from_dict(df_dict)
