"""This file is a wrapper for the csv_to_hdf.py, it ensures that the conversion from csv to hdf is run with the correct UCLCHEM version.

"""

import yaml
import pathlib
import subprocess
from argparse import ArgumentParser, RawTextHelpFormatter


def get_parser():
    info = """
    A wrapper that runs `csv_to_hdf.py` given a virtual environment path,
    the underlying script takes uclchem ouptut .csv files, and then converts them to HDF datasets.
    The configuration files are of the format:
        # Whether or not to run the uclchem script
        run: True 
        # The path of the virtual environment
        venvpath : "/data2/vermarien/uclchem-dev/v3.1.0/.venv"  
        # The directory where the uclchem version (installed in the venv) is located
        uclchemdir : "/data2/vermarien/uclchem-dev/v3.1.0/"
        # The output directory, if run is true, this should be where the script outputs the csv files
        outputdir : "/data2/vermarien/uclchem-dev/v3.1.0/examples/test-output"
        # Where to write the output hdf files to
        hdf5root : "output_files"
        # What name to give the hdf dataset.
        runname : "v3.1.0"
        # A comment that is stored in the dataset, useful for non point release versions of UCLCHEM.
        comment: "Version without any adjustments v3.1.0 at checkout 08d37f8c3063f8ff8a9a7aa16d9eff0ed4f99538"""
    parser = ArgumentParser(description=info, formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "configpaths", nargs="+", help="A (list of) configuration file(s)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise NotImplementedError("Currently broken by code changes in io")
    config_files = get_parser()["configpaths"]
    for args in config_files:
        with open(args) as fh:
            config = yaml.safe_load(fh)
        pythonpath = pathlib.Path(config["venvpath"]) / "bin" / "python"
        if config["run"] == True:
            subprocess.run(
                f"cd {config['uclchemdir']}; {pythonpath} scripts/run_uclchem_tests.py",
                shell=True,
            )
        print(f"Opening config {args} with interperter {pythonpath}")
        subprocess.run(f"{pythonpath} csv_to_hdf.py {args}", shell=True)
