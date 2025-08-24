
import logging
from datetime import timedelta
from django.utils import timezone


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




class RightIndentedFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        
        # Add a custom indent to the beginning of the log message
        original_message = super().format(record)
        return f"    {original_message}"  


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
