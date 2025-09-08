from typing import Tuple


class SecondsToTime:
    """
    A class that takes the number of seconds and converts it to either
    its hour, minutes or seconds representation. The class also allows
    it to be displayed in a human readable format.
    
    """
    HOURS_IN_SECONDS = 3600
    SECONDS          = 60

    def __init__(self, seconds: int):
        self._seconds = seconds
    
    @property
    def seconds(self) -> int:
        """Display the time in seconds"""
        return self._seconds % self.SECONDS
    
    @seconds.setter
    def seconds(self, value: int) -> None:
        """
        A setter that takes an integer as a value, and sets it to the seconds
        field in the constructor. This allows the various properties when called to 
        return the value as hours, minutes or seconds.

        Args:
            value (int): The value to be turned into hours, seconds or minutes
        
        Raises:
            A valueError if the value is not an integer or if the value is a ngative
            number or zero

        Returns:
            - Returns None

        Example usage:

        >>> time = SecondsToTime(5025)
        >>> time.seconds
        ... 5025

        >>> time.seconds = 60
        >>> time.seconds
        ... 600
        """
        if not isinstance(value, int):
            raise ValueError(f"Seconds must be an integer, Expected an integer got {type(value).__name__}")
        if value < 0:
            raise ValueError("Seconds must be greater than 0")
        self._seconds = value
        
    @property    
    def hour(self) -> int:
        """Display the time in hours"""
        return self._seconds // self.HOURS_IN_SECONDS
    
    @property
    def minutes(self) -> int:
        """Display the time in minutes"""
        return (self._seconds % self.HOURS_IN_SECONDS) // self.SECONDS
    
    @property
    def hour_minutes_and_seconds(self) -> Tuple[int, int, int]:
        """
        Returns a single tuple containing three integer values.
        Each integer in the tuple represents a single time value 
        e.g the hour, minute and seconds.

        The first integer in the tuple is the hour, the second the minutes
        and the last one the seconds.

        Note:

        The method doesn't return the time in a human readable way just
        a tuple. To return it as a human readable format the
        `format_to_human_readable` method needs to be called.

        Example:
        
        returns (1, 2, 1) => One hour, 2 mimutes and 1 second

        """
        return (self.hour, self.minutes, self.seconds)

    def format_to_human_readable(self) -> str:
        """
        Convert the stored time into a human-readable string.

        Only non-zero time components (hours, minutes, seconds) are included 
        in the output. Zero-valued parts are omitted for readability.

        Examples:

            >>> time = SecondsToTime(3675)
            >>> time.format_to_human_readable()
            '1 hour, 1 minute and 15 seconds'

            >>> time.seconds = 62
            >>> time.format_to_human_readable()
            '1 minute and 2 seconds'

            >>> time.seconds = 5
            >>> time.format_to_human_readable()
            '5 seconds'

        """
        formatted_time =  []

        HOUR_STRING, MIN_STRING, SEC_STRING = "hour", "minute", "second"
        hour, minute, seconds               = self.hour_minutes_and_seconds
        hour_string, min_string, sec_string = None, None, None

        if hour:
            hour_string = self._create_time_string(hour, HOUR_STRING)
        if minute:
            min_string  = self._create_time_string(minute, MIN_STRING)
        if seconds:
            sec_string  = self._create_time_string(seconds, SEC_STRING)
        
        if hour_string is not None:
            formatted_time.append(hour_string)
        if min_string is not None:
            formatted_time.append(min_string)
        if sec_string is not None:
            formatted_time.append(sec_string)

        if len(formatted_time) == 2:
            return " and ".join(formatted_time)    
        elif len(formatted_time) == 3:
            hour_string, minute_string, second_string = formatted_time
            return f"{hour_string}, {minute_string} and {second_string}"
        return "".join(formatted_time)
        
    def _create_time_string(self, time_value: int, identifier: str) -> str:
        """
        Return a human-readable string for a time component.

        Args:
            time_value (int): The value to convert to a string.
            identifier (str): One of 'hour', 'minute', or 'seconds', used to
                            label the time value.

        Raises:
            TypeError: If `time_value` is not an integer.
            ValueError: If `identifier` is not a string or not one of 'hour',
                    'minute', or 'seconds'.

        Examples:
            >>> self._create_time_string(10, "hour")
            '10 hours'

            >>> self._create_time_string(1, "hour")
            '1 hour'

            >>> self._create_time_string("2", "hour")  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
                ...
            TypeError: time_value must be an integer

            >>> self._create_time_string(2, "money")  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
                ...
            ValueError: The identifier must be hour, minutes or seconds. Got an unexpected identifier 'money
        """
    
        if not isinstance(time_value, int):
            raise TypeError(f"The time value must be an int. Expected an integer but got type {type(time_value).__name__}")
        
        if not isinstance(identifier, str):
            raise TypeError(f"The identifier value must be an string. Expected an integer but got type {type(identifier).__name__}")
        
        required_identifiers = ["hour", "minute", "second"]

        if identifier.endswith("s"):
            identifier = identifier[:-1]
        
        if identifier not in required_identifiers:
            raise ValueError(f"The identifier must be hour, minutes or seconds. Got an unexpected identifier {identifier}")
        
        return f"{time_value} {identifier}s" if time_value > 1 else  f"{time_value} {identifier}"

        



    



