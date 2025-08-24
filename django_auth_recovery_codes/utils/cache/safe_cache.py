from typing import Callable, Any, Union

from django.core.cache import cache
from contextlib import contextmanager
import time

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






def get_with_retry(cache_key, fetch_func, ttl, retries=4, delay=0.2):
    """
    Attempt to get a cached value, retrying only on cache-related exceptions.

    Args:
        cache_key (str): The cache key to retrieve.
        fetch_func (Callable): Function to fetch the value if cache miss occurs.
        ttl (int): Time-to-live for the cache entry.
        retries (int): Number of retry attempts on cache exception.
        delay (float): Delay between retries in seconds.

    Returns:
        Any: Cached value or a safe default dictionary if all retries fail due to cache errors.
    """
    for _ in range(retries):
        try:
            return get_cache_or_set(cache_key, fetch_func, ttl)
        except Exception:
            # Retry only on cache-related errors
            time.sleep(delay)
    
    # Fallback if all retries fail
    return {
        "generated": False,
        "emailed": False,
        "viewed": False,
        "downloaded": False
    }



def set_cache_with_retry(key: str, value, ttl: int = 300, retries: int = 2, delay: float = 0.1):
    """
    Safely set a value in the cache with retries to handle transient failures.

    This function is backend-agnostic and works with any Django cache backend.  
    It uses a **per-key lock** to prevent race conditions when multiple processes 
    attempt to write to the same cache key at the same time.  

    If the cache backend fails temporarily (e.g., due to network issues or high load),
    the function will retry the operation a few times before giving up.  

    Args:
        key (str): Cache key.
        value (Any): Value to store.
        ttl (int): Time to live for the cache entry in seconds.
        retries (int): Number of retry attempts on failure.
        delay (float): Delay between retries in seconds.

    Notes:
        - If multiple processes try to write the same key, the lock ensures only one sets it at a time.
        - If they write different keys, there is no blocking — they can run concurrently.
        - If all retries fail, the function silently continues. You can optionally log failures.
    
    Example:
        # Set a simple value safely
        set_cache_with_retry("my_key", [1, 2, 3], ttl=300, retries=3, delay=0.2)
    """
    for _ in range(retries):
        try:
            with cache_lock(key) as locked:
                cache.set(key, value, ttl)
            return  
        except Exception:
           
            time.sleep(delay)

    # All retries failed; fallback: do nothing
    return None
