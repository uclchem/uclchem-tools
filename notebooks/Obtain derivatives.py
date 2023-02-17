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
# cd ~/data2/uclchem-dev/uclchem-tools/.venv/lib/python3.10/site-packages/uclchem

# %%
from uclchemwrap import uclchemwrap as wrap
import numpy as np
import pandas as pd
import os 
from uclchem.analysis import read_output_file

# %%

# %%
df = read_output_file("/home/vermarien/data2/uclchem-dev/compute_rates_of_change/examples/test-output/phase1-full.dat")


# %%
def get_ndot(df):
#     assert all(spec in df.columns for spec in species)
    species_list = list(np.loadtxt(
        "/data2/vermarien/uclchem-dev/uclchem-tools/.venv/lib/python3.10/site-packages/uclchem/species.csv",
        usecols=[0],
        dtype=str,
        skiprows=1,
        unpack=True,
        delimiter=",",
        comments="%",
    ))
    param_dict = {
        "endatfinaldensity": False,
        "freefall": True,
        "initialdens": 1e4,
        "initialtemp": 10.0,
        "finaldens": 1e5,
        "finaltime": 1.0e3,
        "outspecies": len(species_list),
    }
    abundances, success_flag = wrap.cloud(param_dict," ".join(species_list))
    abundances=abundances[:param_dict["outspecies"]] 
    param_dict.pop("outspecies")
    abundancesdot = df.copy()
    for idx, row in df.iterrows():
        input_abund = np.zeros(500)
        row_ = row[species_list]
        input_abund[: len(abundances)] = row_
        rates = wrap.get_odes(param_dict, input_abund)
        abundancesdot.loc[idx, species_list] = rates[:len(abundances)]
    return abundancesdot


# %%
# %%timeit
get_ndot(df)

# %%
ndot = get_ndot(df)

# %%
ndot["Density"] = 0.0
# ndot = np.log10(ndot)
ndot.plot("Time", "H2O")

# %%
from 


# %%

def total_element_abundance(element, df):
    """Calculates that the total elemental abundance of a species as a function of time. Allows you to check conservation.

    Args:
        element (str): Name of element
        df (pandas.DataFrame): DataFrame from `read_output_file()`

    Returns:
        pandas.Series: Total abundance of element for all time steps in df.
    """
    sums = _count_element(df.columns, element)
    for variable in ["Time", "Density", "gasTemp", "av", "point", "SURFACE", "BULK"]:
        sums = np.where(df.columns == variable, 0, sums)
    return df.mul(sums, axis=1).sum(axis=1)

def _count_element(species_list, element):
    """
    Count the number of atoms of an element that appear in each of a list of species,
    return the array of counts

    :param  species_list: (iterable, str), list of species names
    :param element: (str), element

    :return: sums (ndarray) array where each element represents the number of atoms of the chemical element in the corresponding element of species_list
    """
    species_list = pd.Series(species_list)
    # confuse list contains elements whose symbols contain the target eg CL for C
    # We count both sets of species and remove the confuse list counts.
    confuse_list = [x for x in elementList if element in x]
    confuse_list = sorted(confuse_list, key=lambda x: len(x), reverse=True)
    confuse_list.remove(element)
    sums = species_list.str.count(element)
    for i in range(2, 10):
        sums += np.where(species_list.str.contains(element + f"{i:.0f}"), i - 1, 0)
    for spec in confuse_list:
        sums += np.where(species_list.str.contains(spec), -1, 0)
    return sums

elementList = [
    "H",
    "D",
    "HE",
    "C",
    "N",
    "O",
    "F",
    "P",
    "S",
    "CL",
    "LI",
    "NA",
    "MG",
    "SI",
    "PAH",
    "15N",
    "13C",
    "18O",
    "SURFACE",
    "BULK",
]


def test_ode_conservation(element_list=["H", "N", "C", "O"]):
    """Test whether the ODEs conserve elements. Useful to run each time you change network.
    Integrator errors may still cause elements not to be conserved but they cannot be conserved
    if the ODEs are not correct.
    Args:
        element_list (list, optional): A list of elements for which to check the conservation. Defaults to ["H", "N", "C", "O"].
    Returns:
        dict: A dictionary of the elements in element list with values representing the total rate of change of each element.
    """
    species_list = np.loadtxt(
        "/data2/vermarien/uclchem-dev/uclchem-tools/.venv/lib/python3.10/site-packages/uclchem/species.csv",
        usecols=[0],
        dtype=str,
        skiprows=1,
        unpack=True,
        delimiter=",",
        comments="%",
    )
    species_list = list(species_list)
    param_dict = {
        "endatfinaldensity": False,
        "freefall": True,
        "initialdens": 1e4,
        "initialtemp": 10.0,
        "finaldens": 1e5,
        "finaltime": 1.0e3,
        "outspecies": len(species_list),
    }
    abundances, success_flag = wrap.cloud(param_dict," ".join(species_list))
    abundances=abundances[:param_dict["outspecies"]]
    param_dict.pop("outspecies")
    input_abund = np.zeros(500)
    input_abund[: len(abundances)] = abundances
    rates = wrap.get_odes(param_dict, input_abund)
    print(sum(rates!=0.0))
    df = pd.DataFrame(columns=species_list)
    df.loc[len(df)] = rates[: len(species_list)]
    result = {}
    print(df)
    for element in element_list:
        discrep = total_element_abundance(element, df).values
        result[element] = discrep[0]
    return result



# %%
test_ode_conservation()

# %%
# ls -alh ~/data2/uclchem-dev/uclchem-tools/.venv/lib/python3.10/site-packages/uclchem/species.csv

# %%
