from argparse import ArgumentParser, RawTextHelpFormatter
import subprocess
import pathlib
import yaml
import logging
import pandas as pd
from importlib.metadata import version

UCLCHEM_AVAIL = False
try:
    from uclchem.model import cloud, hot_core, collapse, cshock, jshock

    UCLCHEM_AVAIL = True
except ModuleNotFoundError:
    logging.info(
        "We could not find UCLCHEM in this environment, this is fine if you use a venv that has it installed."
    )


def get_model(name):
    return {
        "cloud": cloud,
        "hot_core": hot_core,
        "collapse": collapse,
        "cshock": cshock,
        "jshock": jshock,
    }[name]


def get_parser():
    parser = ArgumentParser(description="info", formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "configpaths", nargs="+", help="A (list of) configuration file(s)"
    )
    parser.add_argument(
        "--venvpath",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # See if we need to run using a venv or not. If so, recall ourselves and use the venv.
    args = get_parser()

    if args.venvpath:
        logging.info(f"Running with virtual environment at {args.venvpath}")
        subprocess.run(
            f"{pathlib.Path(args.venvpath)/'bin/python'} {pathlib.Path(__file__).resolve()} {args.configpaths}",
            shell=True,
        )
    elif UCLCHEM_AVAIL:
        logging.info(f"Running with UCLCHEM version {version('uclchem')}")

        for configpath in args.configpaths:
            with open(configpath) as fh:
                config = yaml.safe_load(fh)
            # retrieve the name of the model, whether it is a key or a dict with additional arguments:
            if isinstance(config["model"], str):
                name = config["model"]
                model_args = {}
            elif isinstance(config["model"], dict):
                name = str(config["model"])
                model_args = config["model"]
            model = get_model(config)
            # Run UCLCHEM
            model(
                param_dict=config["param_dict"],
                out_species=config["model_args"],
                **model_args,
            )
            # CONVERT (csv -> hdf)
            with pd.HDFStore(
                os.path.join(config["hdf5root"], config["runname"] + ".h5")
            ) as store:
                for outputkey in outputfiles:
                    df = read_output_file(
                        os.path.join(
                            config["outputdir"], outputfiles[outputkey] + ".dat"
                        )
                    )
                    store.put(outputkey, df)
                store.get_storer(outputkey).attrs.metadata = config

            # POSTPROCESS UCLCHEM obtain the rates

            # TODO: write analysis
    else:
        logging.warning(
            "No UCLCHEM could be found and no virtualenv with uclchem was specified. Not running any code."
        )
