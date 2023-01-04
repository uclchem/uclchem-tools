if [[ -n $1 ]]; then
    if [[ -e ../../$1 ]]; then
        echo "worktree directory $1 already exists, aborting."
    else
        module load git/2.33.1-GCCcore-11.2.0-nodocs
        if [[ -n $2 ]]; then
            COMMITISH=$2
        else
            COMMITISH=main
        fi
        echo Creating new worktree in ../$1 based on commit $COMMITISH 
        cd ../../root_uclchem &&
        git worktree add -d ../$1 $COMMITISH &&
        cd ../$1 &&
        python -m venv .venv &&
        source .venv/bin/activate &&
        python -m pip install -r requirements.txt &&
        python -m pip install . &&
        python -m pip install -e ../uclchem-tools/ 
    fi
fi