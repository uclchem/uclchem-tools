#!/bin/bash
# Script to generate a new git wortkree based on the root uclchem directory
# Example: script/new_uclchem.sh new_directory_for_branch the_commitish_we_want
if [[ -n $1 ]]; then
    if [[ -e ../$1 ]]; then
        echo "worktree directory $1 already exists, aborting."
    else
        if [[ -n $2 ]]; then
            COMMITISH=$2
        else
            COMMITISH=main
        fi
        echo Creating new worktree in ../$1 based on commit $COMMITISH 
        if [[ -e "../root_uclchem" ]]; then
            echo "Root uclchem already exists, continuing"
        else
            git clone git@github.com:uclchem/uclchem ../root_uclchem
        fi
        cd ../root_uclchem &&
        git worktree add -d ../$1 $COMMITISH &&
        cd ../$1 &&
        python -m venv .venv &&
        source .venv/bin/activate &&
        python -m pip install -r requirements.txt &&
        python -m pip install . &&
        python -m pip install -e ../uclchem-tools/ 
    fi
fi