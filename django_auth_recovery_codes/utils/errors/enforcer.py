from functools import wraps
from typing import get_type_hints, get_origin, get_args, Union
import inspect
from django_auth_recovery_codes.utils.errors.error_messages import construct_raised_error_msg


def _is_instance_of(value, expected_type) -> bool:
    """
    Safe isinstance-like check that supports typing.Union and generics.
    """
    origin = get_origin(expected_type)

    # If not a typing construct, normal isinstance
    if origin is None:
        return isinstance(value, expected_type)

    # Handle Union / Optional
    if origin is Union:
        return any(_is_instance_of(value, arg) for arg in get_args(expected_type))

    # Handle parametrised generics like list[int], dict[str, int]
    return isinstance(value, origin)


def enforce_types(non_null: bool = True):
    """
    Decorator factory to enforce type checks on function parameters.

    Args:
        non_null (bool): If True (default), raises TypeError when a parameter is None.

    Features:
        - Enforces annotated parameter types (int, str, bool, float, list, dict, UUID, datetime, etc.).
        - Supports Union, Optional, and generics (list[int], dict[str, int]).
        - Lazy caching of type hints to avoid forward-reference issues.
        - Consistent error message construction via construct_raised_error_msg.
        - Correctly handles default arguments using inspect.signature.apply_defaults().
    """

    def decorator(func):
        cached_hints = None
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal cached_hints
            if cached_hints is None:
                cached_hints = get_type_hints(func)

            # Bind args/kwargs to signature and apply defaults
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()
            all_args = bound_args.arguments

            for arg_name, expected_type in cached_hints.items():
                if arg_name == "return":
                    continue

                value = all_args.get(arg_name)

                if value is None:
                    if non_null:
                        raise TypeError(f"Argument `{arg_name}` cannot be None.")
                    else:
                        continue  # allow None if non_null=False

                if not _is_instance_of(value, expected_type):
                    raise TypeError(
                        construct_raised_error_msg(
                            arg_name,
                            expected_types=str(expected_type),
                            value=type(value),
                        )
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator
