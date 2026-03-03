"""
Main API facade for pyshort URL shortener.

This module provides the URLShortener class which integrates all components:
- Storage backend for persisting URLs
- URL validator for validating and normalizing URLs
- Code generator for creating short codes
- Statistics tracker for monitoring URL usage
"""
from typing import Optional, Dict, Any

from pyshort.generator import (
    generate_random_code,
    generate_custom_code,
    InvalidCustomCodeError,
)
from pyshort.models import ShortURL, InvalidURLError
from pyshort.storage import (
    StorageBase,
    DictStorage,
    NotFoundError,
    DuplicateCodeError,
    StorageError,
)
from pyshort.stats import StatisticsTracker
from pyshort.validator import (
    URLValidator,
    ValidationError,
    InvalidSchemeError,
    InvalidDomainError,
    BlockedDomainError,
)


class URLShortenerError(Exception):
    """Base exception for URL shortener operations."""
    pass


class InvalidURLOrCodeError(URLShortenerError):
    """Exception raised for invalid URL or code input."""
    pass


class CodeAlreadyExistsError(URLShortenerError):
    """Exception raised when attempting to use an already existing custom code."""
    pass


class ResolveError(URLShortenerError):
    """Exception raised when failing to resolve a short code."""
    pass


class StatisticsError(URLShortenerError):
    """Exception raised for statistics-related errors."""
    pass


class URLShortener:
    """
    Main facade class for the URL shortener.

    This class integrates all components (storage, validator, generator, stats)
    to provide a simple, cohesive API for URL shortening operations.

    Attributes:
        storage: Storage backend for persisting URLs
        validator: URL validator for validating and normalizing URLs
        stats: Statistics tracker for monitoring URL usage

    Example:
        >>> shortener = URLShortener()
        >>> code = shortener.shorten("https://example.com")
        >>> url = shortener.resolve(code)
        >>> stats = shortener.get_stats(code)
    """

    def __init__(
        self,
        storage: Optional[StorageBase] = None,
        validator: Optional[URLValidator] = None,
        stats: Optional[StatisticsTracker] = None,
        default_code_length: int = 6,
        custom_code_min_length: int = 1,
        custom_code_max_length: int = 32,
    ) -> None:
        """
        Initialize the URLShortener.

        Args:
            storage: Storage backend. If None, creates a DictStorage instance.
            validator: URL validator. If None, creates a default URLValidator.
            stats: Statistics tracker. If None, creates a StatisticsTracker.
            default_code_length: Default length for randomly generated codes.
            custom_code_min_length: Minimum length for custom codes.
            custom_code_max_length: Maximum length for custom codes.

        Raises:
            ValueError: If default_code_length, custom_code_min_length, or
                       custom_code_max_length are invalid.
        """
        if default_code_length < 1 or default_code_length > 32:
            raise ValueError("default_code_length must be between 1 and 32")
        if custom_code_min_length < 1:
            raise ValueError("custom_code_min_length must be at least 1")
        if custom_code_max_length < custom_code_min_length:
            raise ValueError("custom_code_max_length must be >= custom_code_min_length")

        self._storage = storage or DictStorage()
        self._validator = validator or URLValidator()
        self._stats = stats or StatisticsTracker()
        self._default_code_length = default_code_length
        self._custom_code_min_length = custom_code_min_length
        self._custom_code_max_length = custom_code_max_length

    def shorten(
        self,
        url: str,
        custom_code: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> str:
        """
        Shorten a URL and return the short code.

        This method validates the URL, generates or validates a short code,
        stores the mapping, and initializes statistics tracking.

        Args:
            url: The URL to shorten.
            custom_code: Optional custom short code. If None, generates a random code.
            expires_at: Optional expiration date as ISO format string (YYYY-MM-DD).

        Returns:
            The short code for the shortened URL.

        Raises:
            InvalidURLOrCodeError: If the URL is invalid or the custom code format is invalid.
            CodeAlreadyExistsError: If the custom code is already in use.
            URLShortenerError: For other errors during shortening.

        Example:
            >>> code = shortener.shorten("https://example.com")
            >>> code = shortener.shorten("https://example.com", custom_code="mylink")
        """
        # Validate the URL
        try:
            validated_url = self._validator.validate_url(url)
        except (ValidationError, InvalidURLError) as e:
            raise InvalidURLOrCodeError(f"Invalid URL: {e}") from e

        # Generate or validate the short code
        if custom_code:
            try:
                short_code = generate_custom_code(
                    custom_code,
                    min_length=self._custom_code_min_length,
                    max_length=self._custom_code_max_length,
                )
            except InvalidCustomCodeError as e:
                raise InvalidURLOrCodeError(f"Invalid custom code: {e}") from e

            # Check if code already exists
            if self._storage.exists(short_code):
                raise CodeAlreadyExistsError(
                    f"Custom code '{short_code}' is already in use"
                )
        else:
            # Generate a unique random code
            max_attempts = 10
            short_code = None
            for attempt in range(max_attempts):
                short_code = generate_random_code(self._default_code_length)
                if not self._storage.exists(short_code):
                    break
                # Retry if code collision occurs
                if attempt == max_attempts - 1:
                    raise URLShortenerError(
                        f"Failed to generate unique code after {max_attempts} attempts"
                    )

        # Create and save the ShortURL
        try:
            from datetime import datetime
            expires_datetime = None
            if expires_at:
                try:
                    expires_datetime = datetime.fromisoformat(expires_at)
                except ValueError as e:
                    raise InvalidURLOrCodeError(
                        f"Invalid expiration date format: {e}"
                    ) from e

            short_url = ShortURL(
                original_url=validated_url,
                short_code=short_code,
                expires_at=expires_datetime,
            )
            self._storage.save(short_url)
        except (DuplicateCodeError, ValueError, TypeError) as e:
            raise URLShortenerError(f"Failed to save URL: {e}") from e

        return short_code

    def resolve(self, short_code: str, track_click: bool = True) -> str:
        """
        Resolve a short code to its original URL.

        Args:
            short_code: The short code to resolve.
            track_click: If True, tracks the click in statistics (default: True).

        Returns:
            The original URL.

        Raises:
            ResolveError: If the short code is not found or the URL has expired.
            URLShortenerError: For other errors during resolution.

        Example:
            >>> url = shortener.resolve("abc123")
            >>> url
            'https://example.com'
        """
        # Validate short code format
        if not short_code or not isinstance(short_code, str):
            raise ResolveError("Short code must be a non-empty string")

        short_code = short_code.strip()

        try:
            short_url = self._storage.get_by_code(short_code)
        except StorageError as e:
            raise ResolveError(f"Storage error: {e}") from e

        if short_url is None:
            raise ResolveError(f"Short code '{short_code}' not found")

        # Check if URL has expired
        if short_url.is_expired():
            raise ResolveError(f"Short code '{short_code}' has expired")

        # Track the click if requested
        if track_click:
            try:
                self._stats.increment_clicks(short_code)
            except ValueError as e:
                raise URLShortenerError(f"Failed to track click: {e}") from e

        return short_url.original_url

    def get_stats(self, short_code: str) -> Dict[str, Any]:
        """
        Get statistics for a short code.

        Args:
            short_code: The short code to get statistics for.

        Returns:
            A dictionary containing:
                - 'click_count': Total number of clicks
                - 'original_url': The original URL
                - 'created_at': Creation timestamp
                - 'is_expired': Whether the URL has expired

        Raises:
            StatisticsError: If the short code is not found.
            URLShortenerError: For other errors during statistics retrieval.

        Example:
            >>> stats = shortener.get_stats("abc123")
            >>> stats['click_count']
            42
        """
        # Validate short code format
        if not short_code or not isinstance(short_code, str):
            raise StatisticsError("Short code must be a non-empty string")

        short_code = short_code.strip()

        try:
            short_url = self._storage.get_by_code(short_code)
        except StorageError as e:
            raise StatisticsError(f"Storage error: {e}") from e

        if short_url is None:
            raise StatisticsError(f"Short code '{short_code}' not found")

        # Get click statistics
        click_count = self._stats.get_click_stats(short_code)

        return {
            "click_count": click_count,
            "original_url": short_url.original_url,
            "created_at": short_url.created_at.isoformat(),
            "is_expired": short_url.is_expired(),
        }

    def delete(self, short_code: str) -> bool:
        """
        Delete a short code.

        Args:
            short_code: The short code to delete.

        Returns:
            True if the code was deleted, False if it was not found.

        Raises:
            URLShortenerError: For errors during deletion.

        Example:
            >>> deleted = shortener.delete("abc123")
            >>> deleted
            True
        """
        # Validate short code format
        if not short_code or not isinstance(short_code, str):
            raise URLShortenerError("Short code must be a non-empty string")

        short_code = short_code.strip()

        try:
            # Delete from storage
            deleted = self._storage.delete(short_code)

            # Reset statistics (ignore if not tracking)
            if deleted:
                old_count = self._stats.reset_url_stats(short_code)

            return deleted
        except StorageError as e:
            raise URLShortenerError(f"Storage error: {e}") from e

    def get_storage(self) -> StorageBase:
        """
        Get the storage backend.

        Returns:
            The storage backend instance.
        """
        return self._storage

    def get_validator(self) -> URLValidator:
        """
        Get the URL validator.

        Returns:
            The URL validator instance.
        """
        return self._validator

    def get_stats_tracker(self) -> StatisticsTracker:
        """
        Get the statistics tracker.

        Returns:
            The statistics tracker instance.
        """
        return self._stats

    def list_all_urls(self) -> list[Dict[str, Any]]:
        """
        List all shortened URLs with their statistics.

        Returns:
            A list of dictionaries, each containing:
                - 'short_code': The short code
                - 'original_url': The original URL
                - 'click_count': Number of clicks
                - 'created_at': Creation timestamp
                - 'is_expired': Whether the URL has expired

        Raises:
            URLShortenerError: For errors during listing.

        Example:
            >>> urls = shortener.list_all_urls()
            >>> len(urls)
            3
        """
        try:
            all_urls = self._storage.list_all()
        except StorageError as e:
            raise URLShortenerError(f"Storage error: {e}") from e

        result = []
        for short_url in all_urls:
            click_count = self._stats.get_click_stats(short_url.short_code)
            result.append({
                "short_code": short_url.short_code,
                "original_url": short_url.original_url,
                "click_count": click_count,
                "created_at": short_url.created_at.isoformat(),
                "is_expired": short_url.is_expired(),
            })

        return result

    def get_total_clicks(self) -> int:
        """
        Get total clicks across all URLs.

        Returns:
            The total number of clicks.
        """
        return self._stats.get_total_clicks()

    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive statistics summary.

        Returns:
            A dictionary containing:
                - 'total_clicks': Total clicks across all URLs
                - 'total_urls': Number of URLs stored
                - 'total_days': Number of days with recorded activity
                - 'top_urls': Top 5 URLs by click count
                - 'today_clicks': Click count for today
        """
        summary = self._stats.get_stats_summary()
        summary["total_urls"] = self._storage.count()
        return summary

    def __repr__(self) -> str:
        """Return a string representation of the URLShortener."""
        return (
            f"URLShortener(storage={self._storage!r}, "
            f"urls={self._storage.count()}, "
            f"total_clicks={self.get_total_clicks()})"
        )


__all__ = [
    "URLShortener",
    "URLShortenerError",
    "InvalidURLOrCodeError",
    "CodeAlreadyExistsError",
    "ResolveError",
    "StatisticsError",
]