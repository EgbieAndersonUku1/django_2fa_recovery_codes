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


def get_cache(key: str, fetch_func, ttl: int = 300):
    """
    Retrieve a value from cache, and populate it if missing using a fetch function.

    Args:
        key (str): Cache key.
        fetch_func (callable): Function to fetch data if cache miss occurs.
        ttl (int): Time to live for the cache entry in seconds.

    Returns:
        Any: The cached or freshly fetched value.
    """
    value = cache.get(fetch_func())

    if value is None:
        print("new request")
        with cache_lock(key) as locked:

            if locked:
                value = fetch_func()

                if value and isinstance(value, list):
                    value = value[0]
                cache.set(key, value, ttl)
            else:
                # Another process is populating cache: try retrieving if not fallback
                value = cache.get(key) or fetch_func()
    else:
        print("getting from the cache")
        print(value)
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


def delete_cache(key: str):
    """
    Delete a value from cache safely using a lock.

    Args:
        key (str): Cache key to delete.
    """
    with cache_lock(key) as locked:
        if locked:
            cache.delete(key)
