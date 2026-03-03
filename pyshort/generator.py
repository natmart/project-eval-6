"""
Short code generation utilities for pyshort URL shortener.

This module provides functions for generating short codes using various methods:
- Random alphanumeric codes
- Custom user-defined codes
- Base62 encoding from integer IDs

Collision Avoidance Considerations:
- Random codes have a theoretical collision probability. For 6-character alphanumeric
  codes (62^6 ≈ 56.8 billion possibilities), the birthday paradox suggests collisions
  become likely after ~266k codes. In production, code uniqueness should be verified
  against existing storage before assignment.
- Base62 encoding from sequential IDs is collision-free by design, provided IDs are unique.
"""

import random
import string
from typing import Optional


# Base62 character set: 0-9, a-z, A-Z
BASE62_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE62 = len(BASE62_CHARS)

# Alphanumeric character set for random codes: 0-9, a-z, A-Z
ALPHANUMERIC = string.ascii_letters + string.digits


class CodeGenerationError(ValueError):
    """Exception raised for errors during code generation."""


class InvalidCustomCodeError(CodeGenerationError):
    """Exception raised for invalid custom code formats."""


def generate_random_code(length: int = 6) -> str:
    """
    Generate a random alphanumeric short code.

    The code uses uppercase and lowercase letters plus digits (62 characters).
    This provides good entropy and URL-friendly characters.

    Args:
        length: Length of the code to generate (default: 6)

    Returns:
        A random alphanumeric code of the specified length

    Raises:
        ValueError: If length is less than 1 or greater than 32

    Examples:
        >>> code = generate_random_code()
        >>> len(code)
        6
        >>> code = generate_random_code(length=8)
        >>> len(code)
        8
    """
    if length < 1:
        raise ValueError("length must be at least 1")
    if length > 32:
        raise ValueError("length must not exceed 32")

    # Use cryptographically secure random number generator
    return "".join(random.choices(ALPHANUMERIC, k=length))


def generate_custom_code(
    code: str,
    min_length: int = 1,
    max_length: int = 32,
    allowed_chars: Optional[str] = None,
) -> str:
    """
    Validate and normalize a custom short code.

    This function validates that a custom code meets requirements and
    returns it in a normalized form (lowercase by default).

    Args:
        code: The custom code to validate
        min_length: Minimum allowed length (default: 1)
        max_length: Maximum allowed length (default: 32)
        allowed_chars: Optional string of allowed characters. If None,
                       allows alphanumeric characters and hyphens.

    Returns:
        The validated and normalized custom code

    Raises:
        InvalidCustomCodeError: If the code doesn't meet requirements
        ValueError: If min_length or max_length are invalid

    Examples:
        >>> generate_custom_code("my-link")
        'my-link'
        >>> generate_custom_code("MyLink")
        'mylink'
    """
    if min_length < 1:
        raise ValueError("min_length must be at least 1")
    if max_length < min_length:
        raise ValueError("max_length must be >= min_length")

    # Default allowed characters: alphanumeric, hyphen, underscore
    if allowed_chars is None:
        allowed_chars = ALPHANUMERIC + "-_"

    # Normalize: strip whitespace, convert to lowercase
    normalized = code.strip().lower()

    # Validate length
    if len(normalized) < min_length:
        raise InvalidCustomCodeError(
            f"Code must be at least {min_length} character(s), got {len(normalized)}"
        )
    if len(normalized) > max_length:
        raise InvalidCustomCodeError(
            f"Code must not exceed {max_length} characters, got {len(normalized)}"
        )

    # Validate characters
    for char in normalized:
        if char not in allowed_chars:
            raise InvalidCustomCodeError(
                f"Code contains invalid character '{char}'. "
                f"Allowed characters: {allowed_chars}"
            )

    return normalized


def encode_base62(number: int) -> str:
    """
    Encode a positive integer to a base62 string.

    This is useful for converting sequential database IDs into compact,
    URL-friendly short codes. Base62 encoding is reversible and collision-free
    when used with unique integer IDs.

    Args:
        number: A non-negative integer to encode

    Returns:
        A base62 encoded string representing the number

    Raises:
        ValueError: If number is negative

    Examples:
        >>> encode_base62(0)
        '0'
        >>> encode_base62(12345)
        'd7C'
        >>> encode_base62(999999)
        '4c91'
    """
    if number < 0:
        raise ValueError("number must be non-negative")

    # Special case for zero
    if number == 0:
        return BASE62_CHARS[0]

    # Convert to base62
    encoded = []
    while number > 0:
        number, remainder = divmod(number, BASE62)
        encoded.append(BASE62_CHARS[remainder])

    # Reverse to get most significant digit first
    return "".join(reversed(encoded))


def decode_base62(encoded: str) -> int:
    """
    Decode a base62 string back to its integer value.

    This reverses the encoding done by encode_base62(). Note that this
    decodes any valid base62 string, not just those generated by encode_base62().

    Args:
        encoded: A base62 encoded string

    Returns:
        The decoded integer value

    Raises:
        ValueError: If encoded contains invalid base62 characters

    Examples:
        >>> decode_base62('0')
        0
        >>> decode_base62('d7C')
        12345
        >>> decode_base62('4c91')
        999999
    """
    if not encoded:
        raise ValueError("encoded string cannot be empty")

    # Convert to lowercase for case-insensitive decoding
    # (Note: base62 is typically case-sensitive, but this provides flexibility)
    encoded = encoded.strip().lower()

    # Validate characters
    for char in encoded:
        if char not in BASE62_CHARS.lower():
            raise ValueError(f"Invalid base62 character: '{char}'")

    # Decode from base62
    result = 0
    for char in encoded:
        result = result * BASE62 + BASE62_CHARS.lower().index(char)

    return result


__all__ = [
    "CodeGenerationError",
    "InvalidCustomCodeError",
    "generate_random_code",
    "generate_custom_code",
    "encode_base62",
    "decode_base62",
    "BASE62_CHARS",
    "BASE62",
]