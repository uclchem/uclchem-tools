from argparse import ArgumentParser, RawTextHelpFormatter
import subprocess
import pathlib
import yaml
import logging

from importlib.metadata import version

UCLCHEM_AVAIL = False
try:
    import uclchem

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

            # if config["settings"]["to_hdf"]:
            # CONVERT (csv -> hdf)
            csvpath = config["param_dict"]["outputFile"]
            datakey = pathlib.Path(csvpath).stem
            if config["settings"]["hdf_save"] == True:
                hdfpath = csvpath.with_suffix(".hdf5")
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
