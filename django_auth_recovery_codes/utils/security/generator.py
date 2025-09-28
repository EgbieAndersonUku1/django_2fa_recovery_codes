import secrets


from django.conf import settings
from string import punctuation


SAFE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijklmnopqrstuvwzyz23456789"
SAFE_TOKEN    = SAFE_ALPHABET + punctuation


def generate_2fa_secure_recovery_code(code_length: int = 6, group_size: int = 6, separator: str = "-") -> str:
    """

    Generates a cryptographically secure 2FA recovery code.

    Recovery codes are one-time backup codes used when the primary 2FA method
    (e.g., TOTP, hardware token) is unavailable. Each code should be treated
    as sensitive and used only once.

    The code is composed of multiple groups of characters, with each group
    having `code_length` characters (default = 6) and `group_size` total groups
    (default = 6), separated by `separator` (default = "-").

    Characters are chosen from a safe alphabet (A-Z, 2-9) to avoid ambiguous
    characters like I, O, 0, 1, resulting in 32 possible characters per position.
    Uses `secrets.choice` to ensure cryptographic randomness.

    Entropy calculation:
        - Each character: 32 possibilities → 5 bits per character
        - Each group: 6 characters → 30 bits per group
        - Total for 6 groups: 180 bits

    This makes the total number of possible codes ~2**180 (~1.53 x 10**54),
    which is computationally infeasible to brute-force with current technology.
    
    For context the universe is 1.4 x 10**10 old which means that under
    today technologies to brute-force a 180 bit 2FA recovery code it
    will take you longer than the universe has been around.

    :Parameters:
        - code_length (int): The number of characters for each group size.
        - group_size  (int): The total number of groups for each character e.g for each group there is 6 character
        - separator   (str): The delimeter that each group will be separated by e.g dashes
    
    Raises:
        - Raises a ValueError if the code_length and group size are not integer
        - Raises a ValueError if the separator is not a string.
        
    Example usage:
        >>> generate_secure_recovery_code()
        '7G2HJK-9M4PQR-AB2DFG-3HJKLM-6N7PQR-8T2VWX'

        >>> generate_secure_recovery_code(code_length=4, group_size=3, separator=":")
        '4G7H:9M2P:AB3D'
    """
 
    return _generate_secure_string_from_characters_helper(SAFE_ALPHABET, code_length, group_size, separator)
 


def generate_secure_token(code_length: int = 10):
    """
    Generates a cryptographically secure token using a predefined set of characters.
    
    The token consists of multiple segments separated by a specified character, 
    and is generated using `_generate_secure_string_from_characters_helper` 
    to ensure cryptographic randomness.

    Args:
        code_length (int): The length of the code
    Returns:
        str: A cryptographically secure token.
    """
    prefix = "django_auth_recovery_2fa_token__"
    token = _generate_secure_string_from_characters_helper(
        SAFE_TOKEN, code_length=code_length, group_size=10, separator=""
    )
    return f"{prefix}{token}"


def _generate_secure_string_from_characters_helper(characters: str, code_length: int = 6, group_size: int = 6, separator: str = "-"):
    """
    Generates a cryptographically secure string from a given set of characters.
    Utilises `secrets.choice` to ensure cryptographic randomness.

    Args:
        characters (str): A string containing the characters to be used for 
                          generating the secure string.
        code_length (int, optional): The length of each generated segment. Defaults to 6.
        group_size (int, optional): The number of segments to generate. Defaults to 6.
        separator (str, optional): The string used to separate each segment. Defaults to "-".

    Returns:
        str: A cryptographically secure string composed of the specified characters.
    """
    MINIMUM_SECURE_LENGTH = 6

    if not isinstance(characters, str):
        raise TypeError(f"Expected a string from the characters but got object with type {type(characters)}")
    
    if not isinstance(separator, str):
        raise TypeError(f"Expected a string from the seperator but got object with type {type(separator)}")
    
    if not isinstance(code_length, int):
        raise TypeError(f"Expected an integer for the code length but got object with type {type(code_length)}")
    
    if not isinstance(group_size, int):
        raise TypeError(f"Expected an integer for the group size but got object with type {type(group_size)}")
    
    if code_length == 0 or code_length < MINIMUM_SECURE_LENGTH:
        raise ValueError(f"The key is not secure enough. code_length must be {MINIMUM_SECURE_LENGTH} or greater")
    
    secure_code = [
        "".join(secrets.choice(characters) for _ in range(code_length))
        for _ in range(group_size)
    ]

    return separator.join(secure_code)
    

 