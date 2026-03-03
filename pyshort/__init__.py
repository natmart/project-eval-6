"""
pyshort - A Python URL Shortener

A simple and efficient URL shortening library.
"""

from pyshort.models import ShortURL, InvalidURLError
from pyshort.validator import (
    URLValidator,
    ValidationError,
    InvalidSchemeError,
    InvalidDomainError,
    BlockedDomainError,
)
from pyshort.generator import (
    generate_random_code,
    generate_custom_code,
    encode_base62,
    decode_base62,
    CodeGenerationError,
    InvalidCustomCodeError,
)
from pyshort.storage import DictStorage, StorageBase, StorageError, DuplicateCodeError, NotFoundError
from pyshort.stats import StatisticsTracker
from pyshort.api import URLShortener

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Models
    "ShortURL",
    "InvalidURLError",
    # Validator
    "URLValidator",
    "ValidationError",
    "InvalidSchemeError",
    "InvalidDomainError",
    "BlockedDomainError",
    # Generator
    "generate_random_code",
    "generate_custom_code",
    "encode_base62",
    "decode_base62",
    "CodeGenerationError",
    "InvalidCustomCodeError",
    # Storage
    "DictStorage",
    "StorageBase",
    "StorageError",
    "DuplicateCodeError",
    "NotFoundError",
    # Statistics
    "StatisticsTracker",
    # API
    "URLShortener",
]