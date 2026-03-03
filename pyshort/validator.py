"""
URL validation and normalization utilities for pyshort URL shortener.

This module provides comprehensive URL validation including:
- Scheme validation (http/https only)
- Domain format validation
- Blocked domain checking
- URL normalization (lowercasing, trailing slash removal, etc.)
"""

import re
from typing import Optional, Set
from urllib.parse import urlparse, urlunparse


class ValidationError(ValueError):
    """Base exception for URL validation errors."""


class InvalidSchemeError(ValidationError):
    """Exception raised for invalid URL schemes."""


class InvalidDomainError(ValidationError):
    """Exception raised for invalid domain formats."""


class BlockedDomainError(ValidationError):
    """Exception raised when a domain is blocked."""


# Default set of blocked domains (can be overridden)
DEFAULT_BLOCKED_DOMAINS: Set[str] = {
    # Malicious/suspicious domains commonly blocked
    "malicious.example.com",
    "spam.example.com",
    # Add more as needed
}


def validate_scheme(url: str) -> str:
    """
    Validate that the URL uses an acceptable scheme (http or https).

    Args:
        url: The URL string to validate

    Returns:
        The parsed URL object

    Raises:
        InvalidSchemeError: If the URL scheme is not http or https
        ValidationError: If the URL has no scheme
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")

    parsed = urlparse(url.strip())

    if not parsed.scheme:
        raise InvalidSchemeError(
            f"URL must include a scheme (http or https): {url}"
        )

    if parsed.scheme.lower() not in ("http", "https"):
        raise InvalidSchemeError(
            f"URL scheme must be http or https, got '{parsed.scheme}': {url}"
        )

    return url


def validate_domain_format(url: str) -> str:
    """
    Validate that the URL has a properly formatted domain.

    This checks for:
    - Presence of netloc (network location)
    - Valid domain name format (labels, TLD)
    - Valid hostname (not IP address format issues)

    Args:
        url: The URL string to validate

    Returns:
        The validated URL string

    Raises:
        InvalidDomainError: If the domain format is invalid
        ValidationError: If the URL has no netloc
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")

    parsed = urlparse(url.strip())

    if not parsed.netloc:
        raise InvalidDomainError(
            f"URL must include a domain or network location: {url}"
        )

    # Validate domain format using regex
    # This allows:
    # - Standard domain names (example.com)
    # - Subdomains (sub.example.com)
    # - International domain names (punycode)
    # - Localhost for development
    
    # IPv6 address format - check before splitting on ':'
    if parsed.netloc.startswith("[") and parsed.netloc.endswith("]"):
        return url

    # Remove port if present (after IPv6 check)
    domain = parsed.netloc.split(":")[0]

    # Allow localhost and IP addresses for development/testing
    if domain in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return url

    # IPv4 address format
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ipv4_pattern, domain):
        # Validate each octet
        octets = domain.split(".")
        try:
            if all(0 <= int(octet) <= 255 for octet in octets):
                return url
            else:
                raise InvalidDomainError(
                    f"Invalid IPv4 address - octets must be 0-255: {domain}"
                )
        except ValueError:
            # If conversion fails, treat as invalid domain
            raise InvalidDomainError(
                f"Invalid IPv4 address format: {domain}"
            )

    # Domain name validation (RFC 1035 compliant)
    # Allows international domain names in punycode format
    domain_label_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$"

    labels = domain.split(".")

    if len(labels) < 2:
        raise InvalidDomainError(
            f"Domain must have at least two labels (e.g., example.com): {domain}"
        )

    # Validate each label
    for i, label in enumerate(labels):
        if not label:
            raise InvalidDomainError(
                f"Domain label cannot be empty: {domain}"
            )

        if len(label) > 63:
            raise InvalidDomainError(
                f"Domain label cannot exceed 63 characters: '{label}' in {domain}"
            )

        # TLD (last label) should not start or end with a hyphen
        if i == len(labels) - 1:
            if label.startswith("-") or label.endswith("-"):
                raise InvalidDomainError(
                    f"TLD cannot start or end with hyphen: {label}"
                )

        if not re.match(domain_label_pattern, label):
            raise InvalidDomainError(
                f"Invalid domain label format: '{label}' in {domain}"
            )

    return url


def is_domain_blocked(
    url: str,
    blocked_domains: Optional[Set[str]] = None
) -> bool:
    """
    Check if the URL's domain is in the blocked domains list.

    This checks for exact domain matches and subdomain matches.
    For example, if "example.com" is blocked, then "sub.example.com"
    is also considered blocked.

    Args:
        url: The URL string to check
        blocked_domains: Set of blocked domains. If None, uses DEFAULT_BLOCKED_DOMAINS

    Returns:
        True if the domain is blocked, False otherwise

    Examples:
        >>> is_domain_blocked("http://example.com", {"example.com"})
        True
        >>> is_domain_blocked("http://sub.example.com", {"example.com"})
        True
        >>> is_domain_blocked("http://other.com", {"example.com"})
        False
    """
    if not url or not isinstance(url, str):
        return False

    parsed = urlparse(url.strip())
    if not parsed.netloc:
        return False

    domain = parsed.netloc.split(":")[0].lower()  # Remove port and lowercase

    # Use provided blocked domains or default
    blocked = blocked_domains if blocked_domains is not None else DEFAULT_BLOCKED_DOMAINS

    # Check exact match
    if domain in blocked:
        return True

    # Check subdomain match
    # If "example.com" is blocked, "sub.example.com" should also be blocked
    for blocked_domain in blocked:
        blocked_domain = blocked_domain.lower()
        if domain == blocked_domain or domain.endswith(f".{blocked_domain}"):
            return True

    return False


def normalize_url(url: str) -> str:
    """
    Normalize a URL by:
    - Lowercasing the scheme and domain
    - Removing trailing slashes from the path
    - Preserving query parameters and fragments

    Args:
        url: The URL string to normalize

    Returns:
        The normalized URL string

    Raises:
        ValidationError: If the URL is invalid

    Examples:
        >>> normalize_url("HTTP://EXAMPLE.COM/path/")
        'http://example.com/path'
        >>> normalize_url("https://Example.com/path/")
        'https://example.com/path'
        >>> normalize_url("https://example.com/path?query=1")
        'https://example.com/path?query=1'
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")

    # Parse the URL
    parsed = urlparse(url.strip())

    # Normalize scheme to lowercase
    scheme = parsed.scheme.lower()

    # Normalize domain to lowercase
    netloc = parsed.netloc.lower()

    # Normalize path: remove trailing slashes
    # urlunparse will handle empty path correctly
    path = parsed.path.rstrip("/") if parsed.path else ""

    # Keep query and fragments as-is
    # Query parameters are case-sensitive, so we preserve them
    query = parsed.query
    fragment = parsed.fragment

    # Reconstruct the URL
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))

    return normalized


def validate_url(
    url: str,
    blocked_domains: Optional[Set[str]] = None,
    normalize: bool = True
) -> str:
    """
    Comprehensive URL validation including scheme, domain, and blocked domain checks.

    This is the main validation function that combines all validation checks.

    Args:
        url: The URL string to validate
        blocked_domains: Optional set of blocked domains to check against
        normalize: If True, normalize the URL (default: True)

    Returns:
        The validated and optionally normalized URL string

    Raises:
        InvalidSchemeError: If the URL scheme is not http or https
        InvalidDomainError: If the domain format is invalid
        BlockedDomainError: If the domain is blocked
        ValidationError: For other validation errors

    Examples:
        >>> validate_url("https://example.com")
        'https://example.com'
        >>> validate_url("ftp://example.com")
        InvalidSchemeError: URL scheme must be http or https
        >>> validate_url("http://blocked.com", blocked_domains={"blocked.com"})
        BlockedDomainError: Domain 'blocked.com' is blocked
    """
    # Validate scheme
    validate_scheme(url)

    # Validate domain format
    validate_domain_format(url)

    # Check for blocked domains
    if is_domain_blocked(url, blocked_domains):
        parsed = urlparse(url.strip())
        domain = parsed.netloc.split(":")[0].lower()
        raise BlockedDomainError(f"Domain '{domain}' is blocked")

    # Normalize URL if requested
    if normalize:
        result = normalize_url(url)
    else:
        result = url.strip()

    return result


class URLValidator:
    """
    URL validator class with configurable blocked domains list.

    This class provides a more object-oriented interface for URL validation
    with persistent configuration (like blocked domains).

    Attributes:
        blocked_domains: Set of domains that are blocked

    Examples:
        >>> validator = URLValidator(blocked_domains={"spam.com"})
        >>> validator.validate_url("https://example.com")
        'https://example.com'
        >>> validator.validate_url("https://spam.com")
        BlockedDomainError: Domain 'spam.com' is blocked
    """

    def __init__(
        self,
        blocked_domains: Optional[Set[str]] = None,
        normalize_by_default: bool = True
    ):
        """
        Initialize the URLValidator.

        Args:
            blocked_domains: Set of domains to block. If None, uses DEFAULT_BLOCKED_DOMAINS
            normalize_by_default: Whether to normalize URLs by default in validate_url()
        """
        self.blocked_domains = (
            blocked_domains.copy() if blocked_domains else DEFAULT_BLOCKED_DOMAINS.copy()
        )
        self.normalize_by_default = normalize_by_default

    def validate_scheme(self, url: str) -> str:
        """
        Validate the URL scheme (http or https only).

        Args:
            url: The URL string to validate

        Returns:
            The URL string

        Raises:
            InvalidSchemeError: If the scheme is invalid
        """
        return validate_scheme(url)

    def validate_domain_format(self, url: str) -> str:
        """
        Validate the domain format.

        Args:
            url: The URL string to validate

        Returns:
            The URL string

        Raises:
            InvalidDomainError: If the domain format is invalid
        """
        return validate_domain_format(url)

    def is_domain_blocked(self, url: str) -> bool:
        """
        Check if the URL's domain is blocked.

        Args:
            url: The URL string to check

        Returns:
            True if the domain is blocked, False otherwise
        """
        return is_domain_blocked(url, self.blocked_domains)

    def normalize_url(self, url: str) -> str:
        """
        Normalize the URL.

        Args:
            url: The URL string to normalize

        Returns:
            The normalized URL string

        Raises:
            ValidationError: If the URL is invalid
        """
        return normalize_url(url)

    def validate_url(
        self,
        url: str,
        normalize: Optional[bool] = None
    ) -> str:
        """
        Comprehensive URL validation.

        Args:
            url: The URL string to validate
            normalize: If True, normalize the URL. If None, uses normalize_by_default

        Returns:
            The validated and optionally normalized URL string

        Raises:
            InvalidSchemeError: If the scheme is invalid
            InvalidDomainError: If the domain format is invalid
            BlockedDomainError: If the domain is blocked
            ValidationError: For other validation errors
        """
        should_normalize = (
            normalize if normalize is not None else self.normalize_by_default
        )
        return validate_url(url, self.blocked_domains, should_normalize)

    def add_blocked_domain(self, domain: str) -> None:
        """
        Add a domain to the blocked domains list.

        Args:
            domain: The domain to block (will be lowercased)
        """
        if domain:
            self.blocked_domains.add(domain.lower().strip())

    def remove_blocked_domain(self, domain: str) -> None:
        """
        Remove a domain from the blocked domains list.

        Args:
            domain: The domain to unblock
        """
        self.blocked_domains.discard(domain.lower().strip())

    def get_blocked_domains(self) -> Set[str]:
        """
        Get a copy of the blocked domains list.

        Returns:
            Set of blocked domains
        """
        return self.blocked_domains.copy()

    def set_blocked_domains(self, domains: Set[str]) -> None:
        """
        Set the blocked domains list.

        Args:
            domains: Set of domains to block
        """
        self.blocked_domains = {d.lower().strip() for d in domains if d.strip()}


__all__ = [
    "ValidationError",
    "InvalidSchemeError",
    "InvalidDomainError",
    "BlockedDomainError",
    "DEFAULT_BLOCKED_DOMAINS",
    "validate_scheme",
    "validate_domain_format",
    "is_domain_blocked",
    "normalize_url",
    "validate_url",
    "URLValidator",
]