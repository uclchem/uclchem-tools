import yaml
import os
import sys
import pkg_resources
import subprocess

if __name__ == "__main__":
    for args in sys.argv[1:]:
        with open(args) as fh:
            config = yaml.safe_load(fh)
        pythonpath = str(config["venvpath"]) + '/bin/python'
        if config["run"] == True:
            subprocess.run(f"cd {config['uclchemdir']}; {pythonpath} scripts/run_uclchem_tests.py; {pythonpath} -m pip install tables", shell=True)
        print(f"Opening config {args} with interperter {pythonpath}")
        subprocess.run(f"{pythonpath} csv_to_hdf.py {args}", shell=True)