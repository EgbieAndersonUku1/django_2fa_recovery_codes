from __future__ import annotations 

from django.contrib.auth import get_user_model
from django.db import models
from typing import TypeVar, Generic
from django.conf import settings

from django_auth_recovery_codes.base_models import flush_cache_and_write_attempts_to_db, AbstractBaseModel
from django_auth_recovery_codes.utils.cooldown_period import RecoveryCooldownManager
from django_auth_recovery_codes.loggers.loggers import attempt_guard_logger
from django_auth_recovery_codes.utils.converter import SecondsToTime
from django_auth_recovery_codes.utils.cache.safe_cache import get_cache_with_retry


MULTIPLIER  = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER", 2)
CUTOFF      = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT", 3600)

T = TypeVar("T", bound=models.Model)

cooldown_manager = RecoveryCooldownManager(multiplier=MULTIPLIER, cutoff=CUTOFF, logger=attempt_guard_logger)


User = get_user_model()


class AttemptGuard(Generic[T]):
    """
    Generic attempt guard for throttling user actions.

    Purpose:
        Prevent users from spamming sensitive actions (e.g., login attempts,
        recovery codes, password resets) by enforcing a cooldown period.

    How it works:
        1. Checks cache first to see if the user is in a cooldown (fast path).
        2. Falls back to the database if no cache entry exists or cooldown expired.
        3. Updates attempt counts and cooldown in both cache and database.

    Requirements:
        The model passed as 'instance' must implement:
            - get_by_user(user): returns the instance for the given user or None
            - get_remaining_time_till_next_attempt(): returns cooldown in seconds

        The model must have a field to track attempt counts and must be passed into
        the constructor.

    Generic:
        T can be any Django model. Runtime checks ensure required methods exist,
        making this guard reusable across different user actions.
    """

    def __init__(self, instance_attempt_field_name: str, instance: T):
        """
        Initialise the AttemptGuard.

        Args:
            cache_key (str): The cache key used for storing attempts and cooldown.
            instance_attempt_field_name (str): The name of the field on the model that tracks attempts.
            instance (T): The Django model instance to guard (must implement required methods).

        Raises:
            TypeError: If the model does not implement get_by_user.
            AttributeError: If the instance does not have the attempt field.
        """
        if not hasattr(instance, instance_attempt_field_name):
            raise AttributeError(
                f"The instance doesn't have a field named '{instance_attempt_field_name}'"
            )
        
        if not hasattr(instance, "get_by_user"):
            raise TypeError(f"{instance.__class__.__name__} must implement get_by_user()"
            )
        
        self._instance: T        = instance
        self.attempt_field_name  = instance_attempt_field_name
        self._cache_key          = None

    def _increment_attempts(self, user_instance: T) -> None:
        """
        Increment the attempt counter on the instance and save to the database.

        Args:
            user_instance (T): The model instance representing this user's record.

        Raises:
            AttributeError: If the attempt field is missing.
            Exception: If saving the instance fails.
        """
        try:
            attempts = getattr(user_instance, self.attempt_field_name)
            if attempts is None:
                attempts = 0

            setattr(user_instance, self.attempt_field_name, attempts + 1)
            
            user_instance.save()
        except Exception as e:
            raise Exception(f"Failed to increment attempts: {e}")

    def _process_recovery_cooldown_period(self, remaining_seconds: int, user_instance: T) -> tuple[bool, int]:
        """
        Start the cooldown period for the user.

        Increments the attempt counter and sets the cache TTL to enforce the cooldown.

        Args:
            user_instance (T): The model instance representing this user's record.
            remaining_seconds (int): Number of seconds remaining in the cooldown.

        Returns:
            Tuple[bool, int]: (allowed, remaining cooldown seconds)
        """
        self._increment_attempts(user_instance)

        if cooldown_manager.cache_key:
            cooldown_manager.cache_key = self._cache_key

        cooldown_manager.initial_ttl = remaining_seconds

        return cooldown_manager.start()

    def _build_cache_key(self, action: str, user: User) -> str:
        """
        Returns a fully built unique cache key using user instance and action parameter

        Args:
            user (user): The user instance required to build the cache key
            Action (str): The action used to describe the cache key

        Raises:
            - ValueError if the user instance is not an instance of User and the action is not
              a string
        Returns
            - str
        """
        AbstractBaseModel.is_user_valid(user)

        if not isinstance(action, str):
            raise ValueError(f"The action is not a string. Expected a string got a value with type {type(action).__name__}")
        
        self._cache_key = f"attempts:{action}:{user.id}"
        return self._cache_key
    
    def can_proceed(self, user: User, action: str) -> tuple[bool, int]:
        """
        Check if the user can perform the given action (e.g., login, recovery code).

        Args:
            user (User): The user attempting the action.
            action (str): The action name, used for cache key scoping.

        Returns:
            Tuple[bool, int]: (allowed, remaining cooldown seconds)

        Raises:
            ValueError: If no instance exists for this user.
            TypeError: If required methods are missing on the instance.
        """
        cache_key                  = self._build_cache_key(user=user, action=action)
        cooldown_manager.cache_key = cache_key
        data                       = get_cache_with_retry(cache_key, default={})
        attempts                   = data.get("attempts", 0)
        next_allowed_time          = data.get("remaining_seconds", 0)
        
        # Cached cooldown check
        if attempts > 0 and next_allowed_time > 0:

            wait_time = SecondsToTime(next_allowed_time).format_to_human_readable()
            attempt_guard_logger.debug(f"[CACHE RETRIEVAL] Getting data from cache with user {user.id}. The cache expires in {wait_time} left")
            
            return False, cooldown_manager.update()

        # Database fallback
        user_instance: T | None = self._instance.get_by_user(user)
        if user_instance is None:
            raise ValueError("No instance found for this user")

        if not hasattr(user_instance, "get_remaining_time_till_next_attempt"):
            raise TypeError(f"{user_instance.__class__.__name__} must implement get_remaining_time_till_next_attempt()")
        
        remaining_time = user_instance.get_remaining_time_till_next_attempt()
    
        if remaining_time > 0:

            wait_time = SecondsToTime(remaining_time).format_to_human_readable()

            attempt_guard_logger.debug(f"[DB RETRIEVAL] User {user.id} cooldown period to wait: {wait_time} left")
            return self._process_recovery_cooldown_period(user_instance=user_instance, remaining_seconds=remaining_time)

        attempt_guard_logger.info(f"User {user} is now allowed to attempt another login attempt.")

        flush_cache_and_write_attempts_to_db(instance=user_instance,
                                            field_name=self.attempt_field_name,
                                            cache_key=cache_key,
                                            logger=attempt_guard_logger,
                                            )
        return True, 0
