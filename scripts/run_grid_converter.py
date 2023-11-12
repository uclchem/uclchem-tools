import uclchem_tools
import pandas as pd
from uclchem_tools.io.io import GridConverter
import argparse


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "hdf_path", help="The path to the hdf file to store the grid in"
    )
    parser.add_argument(
        "model_df",
        help="The grid model table that describes the grid. Must be a csv file",
    )
    parser.add_argument(
        "--abundances_dir",
        nargs="?",
        default="default_value",
        help="Optional directory that stores the abundance files, useful in case you moved these since creating the grid.",
    )
    parser.add_argument(
        "--derivatives_dir",
        nargs="?",
        default="default_value",
        help="Optional directory that stores the derivatives files, useful in case you moved these since creating the grid.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_parser()
    GridConverter(**vars(args))
