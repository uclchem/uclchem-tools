import uclchem


def run_model(name, param_dict, outspecies, model_args={}):
    """Simple wrapper that converts the name of a model to the uclchem model itself, then runs it with the options.

    For a general guideline on which parameters to use for everything see: https://uclchem.github.io/docs/parameters

    Args:
        name (str): The model you wish to use
        param_dict (dict[str, Union[float, bool, str]]): An UCLCHEM parameter dictionary
        outspecies (list[str]): A list with the species you wish to write to the output file
        model_args (dict, optional): Optional arguments for the specific model. i.e. temp_idx for hot_core. Defaults to {}.

    Returns:
        _type_: _description_
    """
        # Obtain the model from uclchem wrapper
    model = {
        "cloud": uclchem.model.cloud,
        "hot_core": uclchem.model.hot_core,
        "collapse": uclchem.model.collapse,
        "cshock": uclchem.model.cshock,
        "jshock": uclchem.model.jshock,
    }[name]
    # Run UCLCHEM
    model(
        param_dict=param_dict,
        out_species=outspecies,
        **model_args,
    )
    return model
