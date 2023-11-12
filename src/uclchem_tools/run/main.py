from argparse import ArgumentParser, RawTextHelpFormatter
import importlib
import subprocess
import pathlib
import yaml
import logging

from importlib.metadata import version

UCLCHEM_AVAIL = False
try:
    importlib.util.find_spec("uclchem")

    UCLCHEM_AVAIL = True
except ModuleNotFoundError:
    logging.info(
        "We could not find UCLCHEM in this environment, to resolve this use a venv that has uclchem installed."
    )


def get_cli_parser():
    parser = ArgumentParser(description="info", formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "configpaths", nargs="+", help="A (list of) configuration file(s)", type=str
    )
    parser.add_argument(
        "--venvpath",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # See if we need to run using a venv or not. If so, recall ourselves and use the venv.
    args = get_cli_parser()

    if args.venvpath:
        logging.info(f"Running with virtual environment at {args.venvpath}")
        subprocess.run(
            f"{pathlib.Path(args.venvpath)/'bin/python'} {pathlib.Path(__file__).resolve()} {' '.join(args.configpaths)}",
            shell=True,
        )
    elif UCLCHEM_AVAIL:
        # Only import the rates module if AMUSE is there.
        from model import run_model
        from uclchem_tools.io.io import full_output_csv_to_hdf

        UCLCHEM_VERSION = version("uclchem")
        logging.info(f"Running with UCLCHEM version {UCLCHEM_VERSION}")
        for configpath in args.configpaths:
            with open(configpath) as fh:
                config = yaml.safe_load(fh)
            # retrieve the name of the model, whether it is a key or a dict with additional arguments:
            if config["settings"]["run_model"]:
                if isinstance(config["model"], str):
                    name = config["model"]
                    model_args = {}
                elif isinstance(config["model"], dict):
                    name = str(list(config["model"].keys())[0])
                    model_args = config["model"][name]
                run_model(
                    name,
                    config["param_dict"],
                    config["outspecies"],
                    model_args,
                )

            # Retrieve the name of the output file and convert it to hdf5 if requested:
            csvpath = config["param_dict"]["outputFile"]
            # The datakey is the name of the file without the extension:
            datakey = pathlib.Path(csvpath).stem
            # If the hdf_save is True, we convert the file to a standalone hdf5 in the same directory.
            if config["settings"]["hdf_save"] is True:
                hdfpath = csvpath.with_suffix(".hdf5")
            # If the hdf_save is a string, we save the hdf5 file in the specified directory.
            elif config["settings"]["hdf_save"]:
                hdfpath = config["settings"]["hdf_save"]
            else:
                hdfpath = False
            if hdfpath:
                full_output_csv_to_hdf(
                    csvpath,
                    hdfpath,
                    datakey,
                    get_rates=config["settings"]["get_rates"],
                    assume_identical_networks=True,
                )
    else:
        logging.warning(
            "No UCLCHEM could be found and no virtualenv with uclchem was specified. Not running any code."
        )
