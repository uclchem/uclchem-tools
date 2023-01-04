import pandas as pd
from uclchem.analysis import read_output_file
import yaml
import sys
import os

if __name__=="__main__":
    with open(sys.argv[1]) as fh:
        config = yaml.safe_load(fh)
    print(config)
    outputfiles = {"phase1": "phase1-full", "phase2": "phase2-full", "static": "static-full"}
    with pd.HDFStore(os.path.join(config["hdf5root"], config["runname"] + ".h5")) as store:
        for outputkey in outputfiles:
            df = read_output_file(os.path.join(config["outputdir"], outputfiles[outputkey] + ".dat"))
            store.put(outputkey, df)
        store.get_storer(outputkey).attrs.metadata = config