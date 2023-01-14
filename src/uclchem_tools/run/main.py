from argparse import ArgumentParser, RawTextHelpFormatter
import subprocess
import pathlib
import yaml
import logging
import pandas as pd
from importlib.metadata import version

UCLCHEM_AVAIL = False
try:
    import uclchem

    UCLCHEM_AVAIL = True
except ModuleNotFoundError:
    logging.info(
        "We could not find UCLCHEM in this environment, to resolve this use a venv that has uclchem installed."
    )


def get_model(name):
    return {
        "cloud": uclchem.model.cloud,
        "hot_core": uclchem.model.hot_core,
        "collapse": uclchem.model.collapse,
        "cshock": uclchem.model.cshock,
        "jshock": uclchem.model.jshock,
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
        # Only import the rates module if AMUSE is there.
        from rates import get_rates_of_change, rates_to_dfs

        UCLCHEM_VERSION = version("uclchem")
        logging.info(f"Running with UCLCHEM version {UCLCHEM_VERSION}")
        for configpath in args.configpaths:
            with open(configpath) as fh:
                config = yaml.safe_load(fh)
            # retrieve the name of the model, whether it is a key or a dict with additional arguments:
            if isinstance(config["model"], str):
                name = config["model"]
                model_args = {}
            elif isinstance(config["model"], dict):
                name = str(list(config["model"].keys())[0])
                model_args = config["model"][name]
            # Obtain the model from uclchem
            model = get_model(name)
            # Run UCLCHEM
            print(model.__doc__)
            print(model_args)
            model(
                param_dict=config["param_dict"],
                out_species=config["outspecies"],
                **model_args,
            )
            # CONVERT (csv -> hdf)
            csvpath = config["param_dict"]["outputFile"]
            datakey = pathlib.Path(csvpath).stem
            if config["settings"]["hdf_save"] == True:
                hdfpath = csvpath.with_suffix(".hdf5")
            elif config["settings"]["hdf_save"]:
                hdfpath = config["settings"]["hdf_save"]
            else:
                hdfpath = False
            print(hdfpath)
            with pd.HDFStore(hdfpath) as store:
                df = uclchem.analysis.read_output_file(csvpath)
                store.put(datakey + "/abundances", df)
                print(config)
                store.get_storer(datakey + "/abundances").attrs.metadata = config
                # Add reactions and species from current UCLCHEM install
                reactions = uclchem.utils.get_reaction_table()
                species = uclchem.utils.get_species_table()
                store.put(datakey + "/reactions", reactions)
                store.put(datakey + "/species", species)
                # POSTPROCESS UCLCHEM obtain the rates
                rates_dict = get_rates_of_change(df, species, reactions)
                for specie in list(species["Name"]):
                    df_rates, df_production, df_destruction = rates_to_dfs(
                        rates_dict, specie
                    )
                    store.put(f"{datakey}/{specie}/total_rates", df_rates)
                    store.put(f"{datakey}/{specie}/production)", df_production)
                    store.put(f"{datakey}/{specie}/df_destruction", df_destruction)
    else:
        logging.warning(
            "No UCLCHEM could be found and no virtualenv with uclchem was specified. Not running any code."
        )
