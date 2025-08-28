# 
# Recovery Code Hashing Strategy
# ------------------------------

# We use a *two-step hashing* approach to balance usability (deterministic lookup) 
# with strong security (adaptive password hashing):

# 1. **lookup_hash (HMAC + SHA3-512)**  
#    - Deterministic hash of the recovery code, keyed with a secret from settings.  
#    - Used only for database lookups to find the correct RecoveryCode record.  
#    - Fast and consistent: the same input always produces the same hash.  
#    - Does not by itself provide brute-force resistance (SHA3 is fast).  

# 2. **Django's `make_password` / `check_password`**  
#    - Each recovery code is also stored with Django’s password hasher 
#      (PBKDF2, Argon2, etc. depending on settings).  
#    - This adds salting and computational cost, making offline brute force attacks 
#      far harder if the DB is leaked.  
#    - Once a record is found via `lookup_hash`, we use `check_password` to 
#      securely verify the plaintext code.

# Why two hashes?
# ---------------
# - `lookup_hash` is deterministic → allows querying the DB.  
# - `check_password` is salted + slow → provides strong security.  

# This hybrid ensures:
# - Efficient DB lookups (can’t query by raw plaintext).  
# - Strong protection if the DB is compromised.  
# 

import hashlib, hmac
from django.contrib.auth.hashers import identify_hasher
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


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
    except (ValueError, ImproperlyConfigured):
        return False


def make_lookup_hash(code: str, key = None) -> str:
    """
    Return a deterministic HMAC-SHA3-512 hash of a recovery code.

    Used for quick lookups (e.g., caching, locating candidate rows).
    Not suitable for secure password-style verification.

    Args:
      code: 
    """
    if key is None:
        key = settings.DJANGO_AUTH_RECOVERY_KEY.encode()
    return hmac.new(key, code.encode(), hashlib.sha3_512).hexdigest()


