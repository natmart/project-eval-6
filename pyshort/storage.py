"""
Storage backend implementations for pyshort URL shortener.

This module provides abstract storage interface and in-memory implementation.
"""
from abc import ABC, abstractmethod
from threading import Lock
from typing import Dict, List, Optional

from pyshort.models import ShortURL


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class DuplicateCodeError(StorageError):
    """Exception raised when attempting to save a URL with a duplicate short code."""
    pass


class NotFoundError(StorageError):
    """Exception raised when a requested URL is not found."""
    pass


class StorageBase(ABC):
    """
    Abstract base class defining the storage interface for URL shortener.

    All storage implementations must inherit from this class and implement
    the defined methods.
    """

    @abstractmethod
    def save(self, short_url: ShortURL) -> ShortURL:
        """
        Save a ShortURL object to storage.

        Args:
            short_url: The ShortURL object to save

        Returns:
            The saved ShortURL object (may be modified by storage)

        Raises:
            DuplicateCodeError: If a URL with the same short_code already exists
            StorageError: For other storage-related errors
        """
        pass

    @abstractmethod
    def get_by_code(self, short_code: str) -> Optional[ShortURL]:
        """
        Retrieve a ShortURL object by its short code.

        Args:
            short_code: The short code to look up

        Returns:
            The ShortURL object if found, None otherwise
        """
        pass

    @abstractmethod
    def get_by_url(self, original_url: str) -> Optional[ShortURL]:
        """
        Retrieve a ShortURL object by its original URL.

        Args:
            original_url: The original URL to look up

        Returns:
            The ShortURL object if found, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, short_code: str) -> bool:
        """
        Delete a ShortURL object by its short code.

        Args:
            short_code: The short code of the URL to delete

        Returns:
            True if the URL was deleted, False if it was not found
        """
        pass

    @abstractmethod
    def list_all(self) -> List[ShortURL]:
        """
        List all ShortURL objects in storage.

        Returns:
            A list of all ShortURL objects
        """
        pass

    @abstractmethod
    def exists(self, short_code: str) -> bool:
        """
        Check if a short code exists in storage.

        Args:
            short_code: The short code to check

        Returns:
            True if the short code exists, False otherwise
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get the total number of URLs in storage.

        Returns:
            The number of URLs stored
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all URLs from storage.

        Useful for testing or resetting the storage.
        """
        pass


class DictStorage(StorageBase):
    """
    In-memory storage implementation using a dictionary.

    This implementation stores ShortURL objects in memory using a dictionary
    for fast lookups. It is thread-safe for concurrent access.

    Note: Data is lost when the program exits. Use a persistent storage
    implementation for production use.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory storage."""
        self._urls_by_code: Dict[str, ShortURL] = {}
        self._urls_by_url: Dict[str, ShortURL] = {}
        self._lock = Lock()

    def save(self, short_url: ShortURL) -> ShortURL:
        """
        Save a ShortURL object to in-memory storage.

        Args:
            short_url: The ShortURL object to save

        Returns:
            The saved ShortURL object

        Raises:
            DuplicateCodeError: If a URL with the same short_code already exists
        """
        with self._lock:
            if short_url.short_code in self._urls_by_code:
                raise DuplicateCodeError(
                    f"A URL with short_code '{short_url.short_code}' already exists"
                )

            # Store the ShortURL object
            self._urls_by_code[short_url.short_code] = short_url
            self._urls_by_url[short_url.original_url] = short_url

            return short_url

    def get_by_code(self, short_code: str) -> Optional[ShortURL]:
        """
        Retrieve a ShortURL object by its short code.

        Args:
            short_code: The short code to look up

        Returns:
            The ShortURL object if found, None otherwise
        """
        with self._lock:
            return self._urls_by_code.get(short_code)

    def get_by_url(self, original_url: str) -> Optional[ShortURL]:
        """
        Retrieve a ShortURL object by its original URL.

        Args:
            original_url: The original URL to look up

        Returns:
            The ShortURL object if found, None otherwise
        """
        with self._lock:
            return self._urls_by_url.get(original_url)

    def delete(self, short_code: str) -> bool:
        """
        Delete a ShortURL object by its short code.

        Args:
            short_code: The short code of the URL to delete

        Returns:
            True if the URL was deleted, False if it was not found
        """
        with self._lock:
            short_url = self._urls_by_code.get(short_code)
            if short_url is None:
                return False

            # Remove from both dictionaries
            del self._urls_by_code[short_code]
            del self._urls_by_url[short_url.original_url]

            return True

    def list_all(self) -> List[ShortURL]:
        """
        List all ShortURL objects in storage.

        Returns:
            A list of all ShortURL objects
        """
        with self._lock:
            return list(self._urls_by_code.values())

    def exists(self, short_code: str) -> bool:
        """
        Check if a short code exists in storage.

        Args:
            short_code: The short code to check

        Returns:
            True if the short code exists, False otherwise
        """
        with self._lock:
            return short_code in self._urls_by_code

    def count(self) -> int:
        """
        Get the total number of URLs in storage.

        Returns:
            The number of URLs stored
        """
        with self._lock:
            return len(self._urls_by_code)

    def clear(self) -> None:
        """
        Clear all URLs from storage.

        Useful for testing or resetting the storage.
        """
        with self._lock:
            self._urls_by_code.clear()
            self._urls_by_url.clear()

    def __repr__(self) -> str:
        """
        Return a string representation of the storage.

        Returns:
            A string showing the number of stored URLs
        """
        return f"DictStorage(count={self.count()})"


__all__ = [
    "StorageBase",
    "DictStorage",
    "StorageError",
    "DuplicateCodeError",
    "NotFoundError",
]