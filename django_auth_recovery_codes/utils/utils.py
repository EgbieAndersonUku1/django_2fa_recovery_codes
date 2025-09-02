import uuid
import logging
from datetime import timedelta
from django.utils import timezone
from django_q.models import Schedule, Task


def schedule_future_date(days: int = 0, hours: int = 0, minutes: int = 0):
    """
    Returns a datetime object representing a date in the future from now.

    Args:
        days (int): Number of days to add.
        hours (int): Number of hours to add.
        minutes (int): Number of minutes to add.

    Raises:
        TypeError: If any argument is not an integer.
    """
    for arg_name, arg_value in {'days': days, 'hours': hours, 'minutes': minutes}.items():
        if not isinstance(arg_value, int):
            raise TypeError(f"{arg_name} must be an integer. Got {type(arg_value).__name__} instead.")
    
    return timezone.now() + timedelta(days=days, hours=hours, minutes=minutes)






def create_json_from_attrs(instance, keys: list = None, capitalise_keys: bool = False):
    """
    Create a dictionary from an object's attributes.

    Extracts specified attributes from an object instance and returns them
    as a dictionary. If no keys are provided, all attributes are included.
    Optionally, dictionary keys can be capitalised.

    Args:
        instance (object): The object instance to extract attributes from.
        keys (list, optional): List of attribute names to include. If None,
            all instance attributes are included.
        capitalise_keys (bool, optional): If True, converts dictionary keys
            to uppercase. Defaults to False.

    Returns:
        dict: A dictionary containing the requested attributes and their values.
            Missing attributes in `keys` are set to None.

    Raises:
        TypeError: If `instance` is not an object instance or if `keys` is not a list.

    Examples:
        >>> class Person:
        ...     def __init__(self, name, city):
        ...         self.name = name
        ...         self.city = city

        >>> p = Person("Alice", "London")
        >>> create_json_from_attrs(p, keys=["name"], capitalise_keys=True)
        {'NAME': 'Alice'}
        >>>
        >>> create_json_from_attrs(p)
        {'name': 'Alice', 'city': "London"}
    """
    if not hasattr(instance, "__class__"):
        raise TypeError(f"Expected an instance of a class, got {type(instance).__name__}")

    if keys is not None and not isinstance(keys, list):
        raise TypeError(f"Keys must be a list, got {type(keys).__name__}")

    if keys:
        return {key.upper() if capitalise_keys else key: getattr(instance, key, None)
                for key in keys}

    return instance.__dict__.copy()





def cleanup_old_django_q_task(func_substring: str):
    """
    Delete all Django-Q scheduled and queued tasks whose function path contains the given substring.
    
    Args:
        func_substring (str): Substring of the function path to delete tasks for
                              (e.g., "clean_up_old_audits").
    """
    # Delete scheduled recurring tasks
    schedules_deleted, _ = Schedule.objects.filter(func__contains=func_substring).delete()

    # Delete queued/failed tasks
    tasks_deleted, _ = Task.objects.filter(func__contains=func_substring).delete()

    print(
        f"Deleted {schedules_deleted} scheduled tasks and {tasks_deleted} queued tasks "
        f"matching '{func_substring}'"
    )





def schedule_future_date(days: int = 0, hours: int = 0, minutes: int = 0):
    """
    Returns a datetime object representing a date in the future from now.

    Args:
        days (int): Number of days to add.
        hours (int): Number of hours to add.
        minutes (int): Number of minutes to add.

    Raises:
        TypeError: If any argument is not an integer.
    """
    for arg_name, arg_value in {'days': days, 'hours': hours, 'minutes': minutes}.items():
        if not isinstance(arg_value, int):
            raise TypeError(f"{arg_name} must be an integer. Got {type(arg_value).__name__} instead.")
    
    return timezone.now() + timedelta(days=days, hours=hours, minutes=minutes)





def flatten_to_lines(data):
    """
    Convert a list, list-of-lists, or single element into a list of strings.

    - If `data` is a list of lists, each inner list is joined with spaces.
    - If `data` is a flat list, each element is converted to string.
    - If `data` is a single element (not a list), it is converted to a single-element list.

    Args:
        data (list | str | any): Input data to flatten.

    Returns:
        list[str]: List of strings ready for text or CSV output.

    Raises:
        TypeError: If `data` is not a list, string, or a compatible element.
    """
    if isinstance(data, str):
        return [data]

    if not isinstance(data, list):
        # Allow single elements by converting them to a list
        return [str(data)]

    lines = []
    for item in data:
        if isinstance(item, list):
            lines.append(" ".join(map(str, item)))
        else:
            lines.append(str(item))
    return lines



def create_json_from_attrs(instance, keys: list = None, capitalise_keys: bool = False):
    """
    Create a dictionary from an object's attributes.

    Extracts specified attributes from an object instance and returns them
    as a dictionary. If no keys are provided, all attributes are included.
    Optionally, dictionary keys can be capitalised.

    Args:
        instance (object): The object instance to extract attributes from.
        keys (list, optional): List of attribute names to include. If None,
            all instance attributes are included.
        capitalise_keys (bool, optional): If True, converts dictionary keys
            to uppercase. Defaults to False.

    Returns:
        dict: A dictionary containing the requested attributes and their values.
            Missing attributes in `keys` are set to None.

    Raises:
        TypeError: If `instance` is not an object instance or if `keys` is not a list.

    Examples:
        >>> class Person:
        ...     def __init__(self, name, city):
        ...         self.name = name
        ...         self.city = city

        >>> p = Person("Alice", "London")
        >>> create_json_from_attrs(p, keys=["name"], capitalise_keys=True)
        {'NAME': 'Alice'}
        >>>
        >>> create_json_from_attrs(p)
        {'name': 'Alice', 'city': "London"}
    """
    if not hasattr(instance, "__class__"):
        raise TypeError(f"Expected an instance of a class, got {type(instance).__name__}")

    if keys is not None and not isinstance(keys, list):
        raise TypeError(f"Keys must be a list, got {type(keys).__name__}")

    if keys:
        return {key.upper() if capitalise_keys else key: getattr(instance, key, None)
                for key in keys}

    return instance.__dict__.copy()




def create_unique_string(base: str, length: int = 18) -> str:
    """Append a short unique UUID string to a base name."""

    if not isinstance(base, str):
        raise TypeError(f"Expected a string but got {type(base).__name__}")
    
    # Generate a hex string from UUID, trimmed to `length` chars
    unique_suffix = uuid.uuid4().hex[:length]
    return f"{base}_{unique_suffix}"