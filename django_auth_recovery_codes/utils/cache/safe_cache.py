import logging
import time
from typing import Callable, Any, Union
from django.core.cache import cache
from contextlib import contextmanager


logger = logging.getLogger(__name__)


@contextmanager
def cache_lock(key: str, timeout: int = 5):
    """
    Context manager to acquire a simple lock on a cache key to avoid race conditions.

    Args:
        key (str): The cache key to lock.
        timeout (int): Maximum time in seconds to hold the lock before giving up.

    Yields:
        bool: True if lock acquired, False otherwise.
    """
    lock_key = f"{key}_lock"
    lock_acquired = cache.add(lock_key, "locked", timeout)
    try:
        yield lock_acquired
    finally:
        if lock_acquired:
            cache.delete(lock_key)



def get_cache_or_set(key: str, value_or_func: Union[Any, Callable[[], Any]], ttl: int = 300) -> Any:
    """
    Retrieve a value from cache, and populate it if missing.

    This function is useful when computing the value is expensive (e.g., a database query),
    because it **only calls the fetch function if the cache is empty**. Simply using `cache.get` 
    followed by `cache.set` would always require computing the value, even if it is already cached.

    To avoid race conditions when multiple processes/threads request the same cache key at the same time,
    the function uses a **lock per key**:
        - Only one process acquires the lock for a given key and computes the value if missing.
        - Other processes requesting the same key will wait until the first one finishes,
          then they simply read the cached value.
        - Processes requesting *different keys* are unaffected and run concurrently meaning
         since they have request different keys, they run independently with no blocking.

    This ensures the expensive computation happens **only once per key**, even under high concurrency.

    Args:
        key (str): Cache key.
        value_or_func (Any or Callable): A direct value to cache, or a function to call to get the value if not cached.
        ttl (int): Time to live for the cache entry in seconds.

    Returns:
        Any: The cached or freshly set value.

    Example:
        # Using a callable for an expensive DB query
        active_users = get_cache_or_set(
            "active_users",
            lambda: User.objects.filter(is_active=True).all(),
            ttl=600
        )

        # Using a direct value
        some_list = [1, 2, 3]
        cached_list = get_cache_or_set("my_list", some_list, ttl=300)
    """
    value = cache.get(key)

    if value is None:
        with cache_lock(key) as locked:
            if locked:
                value = cache.get(key)
                if value is None:
                    # Only call if value_or_func is callable, otherwise use it directly
                    value = value_or_func() if callable(value_or_func) else value_or_func

                    cache.set(key, value, ttl)

    return value

def set_cache(key: str, value, ttl: int = 300):
    """
    Set a value in cache safely using a lock to prevent race conditions.

    Args:
        key (str): Cache key.
        value (Any): Value to store.
        ttl (int): Time to live for the cache entry in seconds.
    """
    with cache_lock(key) as locked:
        if locked:
            cache.set(key, value, ttl)
        else:
            # optional: fallback if lock not acquired
            cache.set(key, value, ttl)




def _cache_operation_with_retry(
    key: str,
    operation: Callable[[], None],
    retries: int = 2,
    delay: float = 0.1,
    backoff: float = 2.0,
    log_failures: bool = False,
    action_name: str = "operation"
) -> bool:
    """
    Generic helper to safely perform a cache operation with retries,
    per-key locking, and exponential backoff.

    Args:
        key (str): Cache key.
        operation (Callable): Function that performs the cache action (e.g., set/delete).
        retries (int): Number of retry attempts on failure.
        delay (float): Initial delay between retries in seconds.
        backoff (float): Backoff multiplier applied after each failed attempt.
        log_failures (bool): Whether to log failures after all retries.
        action_name (str): Descriptive name of the action for logging.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    current_delay = delay
    for attempt in range(1, retries + 1):
        try:
            result = None
            with cache_lock(key):
                result = operation()
            return result
        except Exception:
            if attempt < retries:
                time.sleep(current_delay)
                current_delay *= backoff  # Exponential backoff

    if log_failures:
        logger.warning(
            "Failed to %s cache for key '%s' after %d attempts.",
            action_name, key, retries
        )
    return False


def set_cache_with_retry(
    key: str,
    value: Any,
    ttl: int = 300,
    retries: int = 2,
    delay: float = 0.1,
    backoff: float = 2.0,
    log_failures: bool = False
) -> bool:
    """
    Safely set a value in the cache with retries, per-key lock,
    and exponential backoff.

    Returns True if the value was successfully set, False otherwise.
    """
    return _cache_operation_with_retry(
        key,
        lambda: cache.set(key, value, ttl),
        retries=retries,
        delay=delay,
        backoff=backoff,
        log_failures=log_failures,
        action_name="set"
    )


def delete_cache_with_retry(
    key: str,
    retries: int = 2,
    delay: float = 0.1,
    backoff: float = 2.0,
    log_failures: bool = False
) -> bool:
    """
    Safely delete a value from the cache with retries, per-key lock,
    and exponential backoff.

    Returns True if the value was successfully deleted, False otherwise.
    """
    return _cache_operation_with_retry(
        key,
        lambda: cache.delete(key),
        retries=retries,
        delay=delay,
        backoff=backoff,
        log_failures=log_failures,
        action_name="delete"
    )


def get_cache_with_retry(
    key: str,
    default: Any = None,
    retries: int = 2,
    delay: float = 0.1,
    backoff: float = 2.0,
    log_failures: bool = False
) -> Any:
    """
    Safely get a value from the cache with retries, per-key lock,
    and exponential backoff.

    Returns the cached value, or `default` if not found or if all retries fail.
    """
    result = _cache_operation_with_retry(
        key,
        lambda: cache.get(key, default),
        retries=retries,
        delay=delay,
        backoff=backoff,
        log_failures=log_failures,
        action_name="get"
    )
    return result if result is not None else default


def get_safe_cache_ttl(key):

    ttl = None
    if hasattr(cache, "ttl"):  # check if backend supports it since not all cache support ttl
        try:
            ttl = cache.ttl(key)
        except NotImplementedError:
            pass
    return ttl


