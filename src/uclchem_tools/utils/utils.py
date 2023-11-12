""" A copy of some core UCLCHEM function to make this package standalone."""
from uclchem_tools.config import UCLCHEM_MASSES, UCLCHEM_ELEMENTS, UCLCHEM_SYMBOLS
import pandas as pd


def is_number(s) -> bool:
    """Try to convert input to a float, if it succeeds, return True.
    Args:
        s: Input element to check for
    Returns:
        bool: True if a number, False if not.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def molecule_to_constituents(speciesName):
    """Loop through the species' name and work out what its consituent
    atoms are. Then calculate mass and alert user if it doesn't match
    input mass.
    """
    i = 0
    atoms = []
    bracket = False
    bracketContent = []
    # loop over characters in species name to work out what it is made of
    while i < len(speciesName):
        # if character isn't a #,+ or - then check it otherwise move on
        if speciesName[i] not in UCLCHEM_SYMBOLS:
            if i + 1 < len(speciesName):
                # if next two characters are (eg) 'MG' then atom is Mg not M and G
                if speciesName[i : i + 3] in UCLCHEM_ELEMENTS:
                    j = i + 3
                elif speciesName[i : i + 2] in UCLCHEM_ELEMENTS:
                    j = i + 2
                # otherwise work out which element it is
                elif speciesName[i] in UCLCHEM_ELEMENTS:
                    j = i + 1

            # if there aren't two characters left just try next one
            elif speciesName[i] in UCLCHEM_ELEMENTS:
                j = i + 1
            # if we've found a new element check for numbers otherwise print error
            if j > i:
                if bracket:
                    bracketContent.append(speciesName[i:j])
                else:
                    atoms.append(speciesName[i:j])  # add element to list
                if j < len(speciesName):
                    if is_number(speciesName[j]):
                        if int(speciesName[j]) > 1:
                            for k in range(1, int(speciesName[j])):
                                if bracket:
                                    bracketContent.append(speciesName[i:j])
                                else:
                                    atoms.append(speciesName[i:j])
                            i = j + 1
                        else:
                            i = j
                    else:
                        i = j
                else:
                    i = j
            else:
                raise ValueError(
                    f"Contains elements not in element list: {speciesName}"
                )
        else:
            # if symbol is start of a bracketed part of molecule, keep track
            if speciesName[i] == "(":
                bracket = True
                bracketContent = []
                i += 1
            # if it's the end then add bracket contents to list
            elif speciesName[i] == ")":
                # If there is a number after the ending bracket, add the bracket content number of times.
                if is_number(speciesName[i + 1]):
                    for k in range(0, int(speciesName[i + 1])):
                        atoms.extend(bracketContent)
                    i += 2
                else:
                    atoms.extend(bracketContent)
                    i += 1
            # otherwise move on
            else:
                i += 1
    return atoms


def get_molecule_mass(molecule_str):
    constituents = molecule_to_constituents(molecule_str)
    mass = 0
    for atom in constituents:
        mass += UCLCHEM_MASSES[UCLCHEM_ELEMENTS.index(atom)]
    return mass


def get_elemental_occurences(molecule_list, filter_zero_elements=True):
    split_element_list = [molecule_to_constituents(spec) for spec in molecule_list]
    df = pd.DataFrame(columns=UCLCHEM_ELEMENTS)
    for split_elements in split_element_list:
        occurences = {}
        for elem in UCLCHEM_ELEMENTS:
            occurences[elem] = [split_elements.count(elem)]
        df = pd.concat((df, pd.DataFrame.from_dict(occurences, orient="columns")))
    df = df.reset_index(drop=True)
    if filter_zero_elements:
        df = df.loc[:, (df.sum() > 0).values]
    return df
