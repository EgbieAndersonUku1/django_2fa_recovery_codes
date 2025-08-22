
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
        return f"    {original_message}"  # 4 spaces or any amout of space you want
