"""
Basic tests to verify project setup and basic functionality.
"""
import pytest

from pyshort.models import ShortURL, InvalidURLError


def test_short_url_creation():
    """Test basic ShortURL object creation."""
    url = ShortURL(
        original_url="https://example.com",
        short_code="abc123"
    )
    assert url.original_url == "https://example.com"
    assert url.short_code == "abc123"
    assert url.click_count == 0


def test_short_url_string_representation():
    """Test string representation of ShortURL."""
    url = ShortURL("https://example.com", "code")
    assert str(url) == "code -> https://example.com"