import logging

from django_auth_recovery_codes.utils.cache.safe_cache import get_cache_with_retry, set_cache_with_retry


default_logger = logging.getLogger(__name__)


class RecoveryCooldownManager:
    """
    Manages recovery cooldowns with automatic TTL calculation and logging.
    """

    def __init__(self, cache_key: str = None, initial_ttl: int = 60, multiplier: float = 2.0, cutoff: int = 3600, logger: logging.Logger = None):
        """
        Args:
            cache_key (str): Cache key for storing cooldown data.
            initial_ttl (int): Initial TTL in seconds for the first attempt.
            multiplier (float): Factor to multiply TTL for subsequent attempts.
            cutoff (int): Maximum allowed TTL.
            logger (logging.Logger, optional): Logger instance to use.
        """
        self._cache_key  = cache_key
        self._initial_ttl  = initial_ttl
        self._multiplier = multiplier
        self._cutoff     = cutoff
        self._logger     = logger or default_logger

    @property
    def initial_ttl(self):
        return self._initial_ttl
    
    @initial_ttl.setter
    def initial_ttl(self, initial_ttl: int):
        self._is_value_valid_set("_initial_ttl", initial_ttl)

    @property
    def cache_key(self):
        return self._cache_key
    
    @cache_key.setter
    def cache_key(self, cache_key: str):
        if not isinstance(cache_key, str):
            raise TypeError(f"The cache key is not a string. Expected a string instance but got {type(cache_key).__name__}")
        self._cache_key = cache_key
      
    @property
    def multiplier(self):
        return self._multiplier
    
    @multiplier.setter
    def multiplier(self, multiplier):
        self._is_value_valid_set("_multiplier", multiplier)
    
    @property
    def cutoff(self):
        return self._cutoff
    
    @cutoff.setter
    def cutoff(self, cutoff):
        self._is_value_valid_set("_cutoff", cutoff)

    @property
    def logger(self):
        return self._logger
    
    @logger.setter
    def logger(self, logger):
        if not isinstance(logger, logging.Logger):
           raise ValueError(f"Expected a Logger instance, got logger with type {type(logger).__name__}")

    def _is_value_valid_set(self, field_name, value):
        if not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer, Expected an integer got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"{field_name} must be greater than 0")
        
        if not hasattr(self, field_name):
            raise TypeError(f"The field {field_name} could be found in the {self.__class__.__name__} class")
        setattr(self, field_name, value)

    def next_cooldown(self):
        """"""
        return min(int(self.initial_ttl * self.multiplier) or 1, self.cutoff)
    
    def start(self) -> tuple[bool, int]:
        """
        Start the recovery cooldown (first attempt).

        Returns:
            tuple[bool, int]: (success flag, TTL in seconds)
        """
        FIRST_ATTEMPT = 1
        data = {
            "attempts": FIRST_ATTEMPT,
            "remaining_seconds": self.initial_ttl,
        }

        self.logger.info(
            f"Starting recovery cooldown: attempt={FIRST_ATTEMPT}, "
            f"timeout={self.initial_ttl}, data={data}"
        )

        set_cache_with_retry(self.cache_key, value=data, ttl=self.initial_ttl)
        return False, self.initial_ttl

    def update(self) -> int:
        """
        Update the cooldown for subsequent attempts using multiplier and cutoff.

        Returns:
            int: The new TTL in seconds
        """
        data             = get_cache_with_retry(self.cache_key, default={})
        self.initial_ttl = data.get("remaining_seconds", 0)
        attempts         = data.get("attempts", 1) + 1
        new_ttl          = self.next_cooldown()

        data.update({"attempts": attempts, "remaining_seconds": new_ttl})
        set_cache_with_retry(self.cache_key, value=data, ttl=self.initial_ttl)
      
        self.logger.debug(f"[Pre-Update] key={self.cache_key}, data={data}")
        self.logger.info(
            f"[Cooldown Update] key={self.cache_key}, attempts={attempts}, "
            f"prev_ttl={self.initial_ttl}, new_ttl={new_ttl}, multiplier={self.multiplier}, cutoff={self.cutoff}"
        )

        return new_ttl