"""
URL data models for pyshort URL shortener.
"""
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse


class InvalidURLError(ValueError):
    """Exception raised for invalid URL formats."""

    pass


class ShortURL:
    """
    Represents a shortened URL with metadata.

    Attributes:
        original_url: The original long URL to be shortened
        short_code: The unique short code for this URL
        created_at: Datetime when the URL was created
        click_count: Number of times the short URL has been accessed
        expires_at: Optional datetime when the URL expires

    Raises:
        InvalidURLError: If the original_url is not a valid URL format
    """

    def __init__(
        self,
        original_url: str,
        short_code: str,
        created_at: Optional[datetime] = None,
        click_count: int = 0,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """
        Initialize a ShortURL instance.

        Args:
            original_url: The original long URL to be shortened
            short_code: The unique short code for this URL
            created_at: Datetime when the URL was created (defaults to now)
            click_count: Initial click count (defaults to 0)
            expires_at: Optional datetime when the URL expires

        Raises:
            InvalidURLError: If the original_url is not a valid URL format
            ValueError: If click_count is negative
        """
        # Validate URL format
        validated_url = self._validate_url(original_url)
        self.original_url: str = validated_url
        self.short_code: str = short_code
        self.created_at: datetime = created_at or datetime.utcnow()
        self.click_count: int = click_count
        self.expires_at: Optional[datetime] = expires_at

        if click_count < 0:
            raise ValueError("click_count must be non-negative")

    @staticmethod
    def _validate_url(url: str) -> str:
        """
        Validate that a string is a properly formatted URL.

        Args:
            url: The URL string to validate

        Returns:
            The normalized URL string

        Raises:
            InvalidURLError: If the URL is invalid
        """
        if not url or not isinstance(url, str):
            raise InvalidURLError("URL must be a non-empty string")

        # Parse the URL
        parsed = urlparse(url.strip())

        # Check for scheme and netloc (basic URL validation)
        if not parsed.scheme:
            raise InvalidURLError(f"URL must include a scheme (http/https): {url}")

        if parsed.scheme not in ("http", "https"):
            raise InvalidURLError(f"URL scheme must be http or https: {url}")

        if not parsed.netloc:
            raise InvalidURLError(f"URL must include a network location: {url}")

        # Normalize the URL
        return parsed.geturl()

    def increment_clicks(self, count: int = 1) -> int:
        """
        Increment the click counter.

        Args:
            count: Number of clicks to increment by (defaults to 1)

        Returns:
            The new click count

        Raises:
            ValueError: If count is negative
        """
        if count < 0:
            raise ValueError("count must be non-negative")

        self.click_count += count
        return self.click_count

    def is_expired(self) -> bool:
        """
        Check if the short URL has expired.

        Returns:
            True if the URL is expired, False otherwise or if no expiry is set
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def __repr__(self) -> str:
        """
        Return a string representation of the ShortURL.

        Returns:
            A detailed string representation including all attributes
        """
        return (
            f"ShortURL(original_url={self.original_url!r}, "
            f"short_code={self.short_code!r}, "
            f"created_at={self.created_at.isoformat()!r}, "
            f"click_count={self.click_count}, "
            f"expires_at={(self.expires_at.isoformat() if self.expires_at else None)!r})"
        )

    def __str__(self) -> str:
        """
        Return a user-friendly string representation.

        Returns:
            A simplified string representation
        """
        return f"{self.short_code} -> {self.original_url}"


__all__ = ["ShortURL", "InvalidURLError"]