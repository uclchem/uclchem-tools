"""File That contains the often used lists of chemical elements, their masses and UCLCHEM symbols
"""
UCLCHEM_MASSES_BY_ELEMENT = {
    "H": 1,
    "D": 2,
    "HE": 4,
    "C": 12,
    "N": 14,
    "O": 16,
    "F": 19,
    "P": 31,
    "S": 32,
    "CL": 35,
    "LI": 3,
    "NA": 23,
    "MG": 24,
    "SI": 28,
    "PAH": 420,
    "15N": 15,
    "13C": 13,
    "18O": 18,
    "E-": 0,
    "FE": 56,
}


def get_uclchem_elements():
    return list(UCLCHEM_MASSES_BY_ELEMENT.keys())


def get_uclchem_masses():
    return list(UCLCHEM_MASSES_BY_ELEMENT.values())


UCLCHEM_SYMBOLS = ["#", "@", "*", "+", "-", "(", ")"]
UCLCHEM_ELEMENTS = get_uclchem_elements()
UCLCHEM_MASSES = get_uclchem_masses()
