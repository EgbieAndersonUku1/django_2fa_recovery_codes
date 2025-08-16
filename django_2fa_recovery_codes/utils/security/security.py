from django.contrib.auth.hashers import identify_hasher


def is_already_hashed(value):
    """
    Determine whether a given string is already a valid Django password hash.

    This function attempts to identify the hashing algorithm and parameters
    from the supplied string using Django's ``identify_hasher`` utility.
    If the string matches the expected format of a Django-generated password
    hash, the function returns ``True``; otherwise, it returns ``False``.

    Args:
        value (str): The string to check, typically a password or password hash.

    Returns:
        bool: ``True`` if the string is a recognised Django password hash,
              ``False`` otherwise.
    """
    try:
        identify_hasher(value)
        return True
    except ValueError:
        return False
