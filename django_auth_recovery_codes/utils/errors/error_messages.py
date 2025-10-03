def construct_raised_error_msg(arg_name, expected_types, value):
    """
    Construct a clear error message for type enforcement.

    Args:
        arg_name (str): Name of the argument.
        expected_types (type | tuple[type] | str): Expected type(s) or a descriptive string.
        value (any): The actual value received.

    Returns:
        str: A formatted error message indicating the expected type(s) and the actual type.
    """
    if isinstance(expected_types, type):
        expected_name = expected_types.__name__
    
    # Handle multiple types in a tuple.,
    elif isinstance(expected_types, tuple):
        expected_name = ", ".join(
            t.__name__ if isinstance(t, type) else str(t)
            for t in expected_types
        )
    
    else:
        expected_name = str(expected_types)

    actual_type_name = type(value).__name__
    return f"Argument `{arg_name}` must be of type {expected_name}, got {actual_type_name} instead."
