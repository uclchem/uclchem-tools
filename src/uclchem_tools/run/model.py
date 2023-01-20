import uclchem


def run_model(name, param_dict, outspecies, model_args={}):
    """Simple wrapper that converts the name of a model to the uclchem model itself, then runs it with the options.

    Args:
        name (_type_): _description_
        param_dict (_type_): _description_
        outspecies (_type_): _description_
        model_args (dict, optional): _description_. Defaults to {}.

    Returns:
        _type_: _description_
    """
    model = {
        "cloud": uclchem.model.cloud,
        "hot_core": uclchem.model.hot_core,
        "collapse": uclchem.model.collapse,
        "cshock": uclchem.model.cshock,
        "jshock": uclchem.model.jshock,
    }[name]

    # Obtain the model from uclchem
    # Run UCLCHEM
    model(
        param_dict=param_dict,
        out_species=outspecies,
        **model_args,
    )
    return model
