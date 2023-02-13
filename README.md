# uclchem-tools

This repository can be used to efficiently interact with UCLCHEM in scenarios where you need to 
interact with UCLCHEM in a reproducible way between development versions or if you need to 
convert large amounts of data originally stored in csv into efficient HDF storage, and later load it.

## List of tools:
- `scripts/new_uclchem.sh` tool to generate new uclchem python environments given one root uclchem clone using the git worktree command. Example: `bash script/new_uclchem.sh directory_with_patch commitish_of_patch`
- `src/uclchem_tools/run/main.py` Run UCLCHEM based on a configuration file as shown in `scripts/smart_configurations/phase1-test.yaml`. This is especially useful for development and comparison across different branches created by the command above, as you can specify which virtual environment should be used.
- `src/uclchem_tools/io/run_csv_to_hdf.py` DEPRECATED, to be replaced with a new tool to convert from csv to HDF>
- `src/io/io.py` File that takes csv outputs from a grid or uclchem run and converts it to HDF storage. This includes loaders to later load the data into memory again.