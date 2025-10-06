from functools import wraps
from typing import get_type_hints, get_origin, get_args, Union
import inspect

def _is_instance_of(value, expected_type) -> bool:
    """
    Enhanced isinstance-like check with support for:
    - Forward references (string-based annotations)
    - typing.Union, Optional, and parametrised generics
    """
    # Forward reference not resolved, skip runtime check
    if isinstance(expected_type, str):
        return True

    origin = get_origin(expected_type)

    # Normal types
    if origin is None:
        return isinstance(value, expected_type)

    if origin is Union:
        return any(_is_instance_of(value, arg) for arg in get_args(expected_type))

    # Handle generics like list[int], dict[str, int]
    return isinstance(value, origin)


def enforce_types(non_null: bool = True):
    """
    Runtime type checker for function parameters.

    - Enforces annotated parameter types.
    - Supports Unions, Optionals, generics, and forward references.
    - Skips None checks if non_null=False.
    """
    def decorator(func):
        sig = inspect.signature(func)
        cached_hints = None

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal cached_hints
            if cached_hints is None:
                try:
                    # Try resolving annotations
                    cached_hints = get_type_hints(func)
                except Exception:
                    # Fall back to raw __annotations__ if resolution fails
                    cached_hints = func.__annotations__

            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()

            for arg_name, expected_type in cached_hints.items():
                if arg_name == "return":
                    continue

                value = bound_args.arguments.get(arg_name)

                if value is None:
                    if non_null:
                        raise TypeError(f"Argument `{arg_name}` cannot be None.")
                    continue

                if not _is_instance_of(value, expected_type):
                    raise TypeError(
                        f"Argument `{arg_name}` expected type {expected_type}, "
                        f"got {type(value).__name__}"
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator
