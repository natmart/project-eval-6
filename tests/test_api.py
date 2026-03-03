"""
Tests for the main URLShortener API module.

These tests cover the full integration of all components (validator, generator,
storage, statistics) through the URLShortener API.
"""

import pytest

from pyshort.api import URLShortener
from pyshort.models import InvalidURLError
from pyshort.storage import NotFoundError
from pyshort.validator import BlockedDomainError
from pyshort.generator import InvalidCustomCodeError
from pyshort.storage import DictStorage
from pyshort.stats import StatisticsTracker
from pyshort.validator import URLValidator


class TestURLShortenerInitialization:
    """Test URLShortener initialization and configuration."""

    def test_default_initialization(self):
        """Test initialization with default components."""
        shortener = URLShortener()

        assert isinstance(shortener.storage, DictStorage)
        assert isinstance(shortener.validator, URLValidator)
        assert isinstance(shortener.stats, StatisticsTracker)
        assert shortener.default_code_length == 6

    def test_custom_storage(self):
        """Test initialization with custom storage."""
        custom_storage = DictStorage()
        shortener = URLShortener(storage=custom_storage)

        assert shortener.storage is custom_storage

    def test_custom_validator(self):
        """Test initialization with custom validator."""
        custom_validator = URLValidator(blocked_domains={"blocked.com"})
        shortener = URLShortener(validator=custom_validator)

        assert shortener.validator is custom_validator

    def test_custom_stats(self):
        """Test initialization with custom stats tracker."""
        custom_stats = StatisticsTracker()
        shortener = URLShortener(stats=custom_stats)

        assert shortener.stats is custom_stats

    def test_custom_code_length(self):
        """Test initialization with custom default code length."""
        shortener = URLShortener(default_code_length=10)

        assert shortener.default_code_length == 10

    def test_invalid_code_length_too_short(self):
        """Test initialization with code length less than 1."""
        with pytest.raises(ValueError, match="default_code_length must be between 1 and 32"):
            URLShortener(default_code_length=0)

    def test_invalid_code_length_too_long(self):
        """Test initialization with code length greater than 32."""
        with pytest.raises(ValueError, match="default_code_length must be between 1 and 32"):
            URLShortener(default_code_length=33)


class TestShortenMethod:
    """Test the shorten() method."""

    def test_shorten_valid_url(self):
        """Test shortening a valid URL."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/very/long/url")

        assert isinstance(short_code, str)
        assert len(short_code) == 6
        assert shortener.exists(short_code)

    def test_shorten_returns_same_code_for_duplicate_url(self):
        """Test that shortening the same URL returns the same code."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example.com/page")
        code2 = shortener.shorten("https://example.com/page")

        assert code1 == code2

    def test_shorten_with_custom_code(self):
        """Test shortening with a custom code."""
        shortener = URLShortener()
        short_code = shortener.shorten(
            "https://example.com/page", custom_code="mylink"
        )

        assert short_code == "mylink"
        assert shortener.exists("mylink")

    def test_shorten_custom_code_normalization(self):
        """Test that custom codes are normalized (lowercase, stripped)."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page", custom_code="  MyLink  ")

        assert short_code == "mylink"

    def test_shorten_different_urls_different_codes(self):
        """Test that different URLs get different codes."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example.com/page1")
        code2 = shortener.shorten("https://example.com/page2")

        assert code1 != code2

    def test_shorten_invalid_format(self):
        """Test shortening an invalid URL format."""
        shortener = URLShortener()

        with pytest.raises(InvalidURLError):
            shortener.shorten("not-a-url")

    def test_shorten_invalid_scheme(self):
        """Test shortening a URL with invalid scheme."""
        shortener = URLShortener()

        with pytest.raises(InvalidURLError):
            shortener.shorten("ftp://example.com/page")

    def test_shorten_blocked_domain(self):
        """Test shortening a URL with blocked domain."""
        validator = URLValidator(blocked_domains={"malicious.com"})
        shortener = URLShortener(validator=validator)

        with pytest.raises(BlockedDomainError):
            shortener.shorten("https://malicious.com/page")

    def test_shorten_invalid_custom_code(self):
        """Test shortening with invalid custom code."""
        shortener = URLShortener()

        with pytest.raises(InvalidCustomCodeError):
            shortener.shorten("https://example.com/page", custom_code="invalid code!")

    def test_shorten_url_normalization(self):
        """Test that URLs are normalized."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://EXAMPLE.COM/page/")
        code2 = shortener.shorten("https://example.com/page")

        # These should be the same due to normalization
        assert code1 == code2


class TestResolveMethod:
    """Test the resolve() method."""

    def test_resolve_valid_code(self):
        """Test resolving a valid short code."""
        shortener = URLShortener()
        original_url = "https://example.com/very/long/url"
        short_code = shortener.shorten(original_url)

        resolved_url = shortener.resolve(short_code)

        assert resolved_url == original_url

    def test_resolve_invalid_code(self):
        """Test resolving a non-existent short code."""
        shortener = URLShortener()

        with pytest.raises(NotFoundError, match="Short code 'nonexistent' not found"):
            shortener.resolve("nonexistent")

    def test_resolve_tracks_click(self):
        """Test that resolving tracks a click in statistics."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        # Resolve twice
        shortener.resolve(short_code)
        shortener.resolve(short_code)

        stats = shortener.get_stats(short_code)
        assert stats["clicks"] == 2

    def test_resolve_without_tracking(self):
        """Test resolving without tracking clicks."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        # Resolve without tracking
        shortener.resolve(short_code, track_click=False)

        stats = shortener.get_stats(short_code)
        assert stats["clicks"] == 0

    def test_resolve_updates_click_count(self):
        """Test that resolving updates the URL's click_count."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        shortener.resolve(short_code)

        info = shortener.get_info(short_code)
        assert info["click_count"] == 1


class TestGetStatsMethod:
    """Test the get_stats() method."""

    def test_get_stats_existing_code(self):
        """Test getting stats for an existing code."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        # Click the URL
        shortener.resolve(short_code)
        shortener.resolve(short_code)
        shortener.resolve(short_code)

        stats = shortener.get_stats(short_code)

        assert stats is not None
        assert isinstance(stats["clicks"], int)
        assert stats["clicks"] == 3
        assert isinstance(stats["daily"], dict)

    def test_get_stats_nonexistent_code(self):
        """Test getting stats for a non-existent code."""
        shortener = URLShortener()

        stats = shortener.get_stats("nonexistent")

        assert stats is None

    def test_get_stats_initial_stats(self):
        """Test that new URLs start with zero clicks."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        stats = shortener.get_stats(short_code)

        assert stats["clicks"] == 0


class TestDeleteMethod:
    """Test the delete() method."""

    def test_delete_existing_code(self):
        """Test deleting an existing short code."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        deleted = shortener.delete(short_code)

        assert deleted is True
        assert not shortener.exists(short_code)

    def test_delete_nonexistent_code(self):
        """Test deleting a non-existent short code."""
        shortener = URLShortener()

        deleted = shortener.delete("nonexistent")

        assert deleted is False

    def test_delete_resets_stats(self):
        """Test that deleting a URL resets its statistics."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        # Click the URL
        shortener.resolve(short_code)
        shortener.resolve(short_code)

        # Delete the URL
        shortener.delete(short_code)

        # Recreate the URL (stats should be reset)
        new_code = shortener.shorten("https://example.com/page")

        stats = shortener.get_stats(new_code)
        assert stats["clicks"] == 0


class TestUpdateURLMethod:
    """Test the update_url() method."""

    def test_update_url_existing_code(self):
        """Test updating the URL for an existing code."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/old/url")

        updated_code = shortener.update_url(short_code, "https://example.com/new/url")

        assert updated_code == short_code
        resolved_url = shortener.resolve(short_code)
        assert resolved_url == "https://example.com/new/url"

    def test_update_url_nonexistent_code(self):
        """Test updating URL for a non-existent code."""
        shortener = URLShortener()

        with pytest.raises(NotFoundError, match="Short code 'nonexistent' not found"):
            shortener.update_url("nonexistent", "https://example.com/new/url")

    def test_update_url_invalid_new_url(self):
        """Test updating with an invalid new URL."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        with pytest.raises(InvalidURLError):
            shortener.update_url(short_code, "not-a-url")

    def test_update_url_blocked_domain(self):
        """Test updating to a URL with blocked domain."""
        validator = URLValidator(blocked_domains={"malicious.com"})
        shortener = URLShortener(validator=validator)
        short_code = shortener.shorten("https://example.com/page")

        with pytest.raises(BlockedDomainError):
            shortener.update_url(short_code, "https://malicious.com/page")


class TestExistsMethod:
    """Test the exists() method."""

    def test_exists_existing_code(self):
        """Test checking if an existing code exists."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        exists = shortener.exists(short_code)

        assert exists is True

    def test_exists_nonexistent_code(self):
        """Test checking if a non-existent code exists."""
        shortener = URLShortener()
        exists = shortener.exists("nonexistent")

        assert exists is False

    def test_exists_after_delete(self):
        """Test that exists returns False after deletion."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        shortener.delete(short_code)
        exists = shortener.exists(short_code)

        assert exists is False


class TestGetInfoMethod:
    """Test the get_info() method."""

    def test_get_info_existing_code(self):
        """Test getting info for an existing code."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        info = shortener.get_info(short_code)

        assert info is not None
        assert info["short_code"] == short_code
        assert info["original_url"] == "https://example.com/page"
        assert "created_at" in info
        assert isinstance(info["click_count"], int)
        assert info["click_count"] == 0

    def test_get_info_nonexistent_code(self):
        """Test getting info for a non-existent code."""
        shortener = URLShortener()

        info = shortener.get_info("nonexistent")

        assert info is None

    def test_get_info_includes_click_count(self):
        """Test that get_info includes updated click count."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        shortener.resolve(short_code)
        shortener.resolve(short_code)

        info = shortener.get_info(short_code)
        assert info["click_count"] == 2


class TestGetAllURLsMethod:
    """Test the get_all_urls() method."""

    def test_get_all_urls_empty(self):
        """Test getting all URLs when storage is empty."""
        shortener = URLShortener()

        urls = shortener.get_all_urls()

        assert urls == {}

    def test_get_all_urls_multiple(self):
        """Test getting all URLs with multiple entries."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example.com/page1")
        code2 = shortener.shorten("https://example.com/page2")
        code3 = shortener.shorten("https://example.com/page3")

        urls = shortener.get_all_urls()

        assert len(urls) == 3
        assert urls[code1] == "https://example.com/page1"
        assert urls[code2] == "https://example.com/page2"
        assert urls[code3] == "https://example.com/page3"

    def test_get_all_urls_after_delete(self):
        """Test that get_all_urls reflects deletions."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example.com/page1")
        code2 = shortener.shorten("https://example.com/page2")

        shortener.delete(code2)

        urls = shortener.get_all_urls()

        assert len(urls) == 1
        assert code1 in urls
        assert code2 not in urls


class TestGetCountMethod:
    """Test the get_count() method."""

    def test_get_count_empty(self):
        """Test getting count when storage is empty."""
        shortener = URLShortener()

        count = shortener.get_count()

        assert count == 0

    def test_get_count_multiple(self):
        """Test getting count with multiple URLs."""
        shortener = URLShortener()
        shortener.shorten("https://example.com/page1")
        shortener.shorten("https://example.com/page2")
        shortener.shorten("https://example.com/page3")

        count = shortener.get_count()

        assert count == 3

    def test_get_count_after_delete(self):
        """Test that get_count reflects deletions."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com/page")
        shortener.shorten("https://example.com/page2")

        shortener.delete(code)

        count = shortener.get_count()

        assert count == 1


class TestResetStatsMethod:
    """Test the reset_stats() method."""

    def test_reset_stats_existing_code(self):
        """Test resetting stats for an existing code."""
        shortener = URLShortener()
        short_code = shortener.shorten("https://example.com/page")

        # Click the URL
        shortener.resolve(short_code)
        shortener.resolve(short_code)
        shortener.resolve(short_code)

        # Reset stats
        reset = shortener.reset_stats(short_code)

        assert reset is True
        stats = shortener.get_stats(short_code)
        assert stats["clicks"] == 0

    def test_reset_stats_nonexistent_code(self):
        """Test resetting stats for a non-existent code."""
        shortener = URLShortener()

        reset = shortener.reset_stats("nonexistent")

        assert reset is False


class TestGetTopURLsMethod:
    """Test the get_top_urls() method."""

    def test_get_top_urls_empty(self):
        """Test getting top URLs when none exist."""
        shortener = URLShortener()

        top_urls = shortener.get_top_urls()

        assert top_urls == {}

    def test_get_top_urls_with_data(self):
        """Test getting top URLs with actual click data."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example.com/page1")
        code2 = shortener.shorten("https://example.com/page2")
        code3 = shortener.shorten("https://example.com/page3")

        # Click different numbers of times
        for _ in range(10):
            shortener.resolve(code1)
        for _ in range(5):
            shortener.resolve(code2)
        for _ in range(15):
            shortener.resolve(code3)

        top_urls = shortener.get_top_urls(limit=5)

        assert len(top_urls) == 3
        assert top_urls[code3] == 15  # Most clicked
        assert top_urls[code1] == 10
        assert top_urls[code2] == 5

    def test_get_top_urls_limit(self):
        """Test that limit parameter works correctly."""
        shortener = URLShortener()
        for i in range(20):
            code = shortener.shorten(f"https://example.com/page{i}")
            for _ in range(i + 1):
                shortener.resolve(code)

        top_urls = shortener.get_top_urls(limit=5)

        assert len(top_urls) == 5


class TestGetTotalStatsMethod:
    """Test the get_total_stats() method."""

    def test_get_total_stats_empty(self):
        """Test getting total stats when no URLs exist."""
        shortener = URLShortener()

        stats = shortener.get_total_stats()

        assert stats["total_urls"] == 0
        assert stats["total_clicks"] == 0
        assert stats["unique_days"] == 0

    def test_get_total_stats_with_data(self):
        """Test getting total stats with actual data."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example.com/page1")
        code2 = shortener.shorten("https://example.com/page2")

        # Click URLs
        shortener.resolve(code1)
        shortener.resolve(code1)
        shortener.resolve(code2)

        stats = shortener.get_total_stats()

        assert stats["total_urls"] == 2
        assert stats["total_clicks"] == 3


class TestClearAllMethod:
    """Test the clear_all() method."""

    def test_clear_all(self):
        """Test clearing all URLs."""
        shortener = URLShortener()
        shortener.shorten("https://example.com/page1")
        shortener.shorten("https://example.com/page2")

        shortener.clear_all()

        assert shortener.get_count() == 0
        assert shortener.get_all_urls() == {}


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_workflow(self):
        """Test a complete URL shortening workflow."""
        shortener = URLShortener()

        # 1. Shorten a URL
        code = shortener.shorten("https://example.com/very/long/path/to/resource")
        assert shortener.exists(code)

        # 2. Resolve the URL
        resolved = shortener.resolve(code)
        assert resolved == "https://example.com/very/long/path/to/resource"

        # 3. Get stats
        stats = shortener.get_stats(code)
        assert stats["clicks"] == 1

        # 4. Resolve again
        shortener.resolve(code)
        stats = shortener.get_stats(code)
        assert stats["clicks"] == 2

        # 5. Get info
        info = shortener.get_info(code)
        assert info["short_code"] == code
        assert info["click_count"] == 2

        # 6. Check total stats
        total = shortener.get_total_stats()
        assert total["total_urls"] == 1
        assert total["total_clicks"] == 2

        # 7. Delete the URL
        deleted = shortener.delete(code)
        assert deleted is True
        assert not shortener.exists(code)

    def test_multiple_urls_workflow(self):
        """Test workflow with multiple URLs."""
        shortener = URLShortener()

        # Create multiple URLs
        codes = []
        for i in range(5):
            code = shortener.shorten(f"https://example.com/page{i}")
            codes.append(code)

        # Click each multiple times
        for i, code in enumerate(codes):
            for _ in(range(i + 1)):
                shortener.resolve(code)

        # Check total count
        assert shortener.get_count() == 5

        # Check total clicks
        total = shortener.get_total_stats()
        assert total["total_clicks"] == 15  # 1 + 2 + 3 + 4 + 5

        # Check top URLs
        top = shortener.get_top_urls(limit=3)
        assert len(top) == 3

        # Delete all
        for code in codes:
            shortener.delete(code)

        assert shortener.get_count() == 0

    def test_custom_code_workflow(self):
        """Test workflow with custom codes."""
        shortener = URLShortener()

        # Create URLs with custom codes
        code1 = shortener.shorten("https://example.com/about", custom_code="about")
        code2 = shortener.shorten("https://example.com/contact", custom_code="contact")

        # Resolve them
        assert shortener.resolve(code1) == "https://example.com/about"
        assert shortener.resolve(code2) == "https://example.com/contact"

        # Update a URL
        shortener.update_url(code1, "https://example.com/about-us")
        assert shortener.resolve(code1) == "https://example.com/about-us"

    def test_error_handling_workflow(self):
        """Test workflow with various error conditions."""
        shortener = URLShortener()

        # Try to resolve non-existent code
        with pytest.raises(NotFoundError):
            shortener.resolve("nonexistent")

        # Try to shorten invalid URL
        with pytest.raises(InvalidURLError):
            shortener.shorten("not-a-url")

        # Try to delete non-existent code
        result = shortener.delete("nonexistent")
        assert result is False

        # Now create a valid URL and try again
        code = shortener.shorten("https://example.com/page")
        result = shortener.resolve(code)
        assert result == "https://example.com/page"
        result = shortener.delete(code)
        assert result is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_url(self):
        """Test shortening a very long URL."""
        long_url = "https://example.com/" + "a" * 1000 + "?param=" + "b" * 1000
        shortener = URLShortener()

        code = shortener.shorten(long_url)
        resolved = shortener.resolve(code)

        assert resolved == long_url

    def test_url_with_unicode(self):
        """Test shortening a URL with unicode characters."""
        shortener = URLShortener()
        # Most validators normalize, but URLs with unicode in path may work
        url = "https://example.com/path-with-dashes-and_underscores"

        code = shortener.shorten(url)
        resolved = shortener.resolve(code)

        assert resolved == url

    def test_minimum_code_length(self):
        """Test using minimum code length (1)."""
        shortener = URLShortener(default_code_length=1)

        # Should generate 1-character codes
        # May get collisions but should work with force=False default
        code = shortener.shorten("https://example.com/page1")

        assert len(code) == 1

    def test_maximum_code_length(self):
        """Test using maximum code length (32)."""
        shortener = URLShortener(default_code_length=32)

        code = shortener.shorten("https://example.com/page")

        assert len(code) == 32

    def test_custom_code_with_special_chars(self):
        """Test custom code with allowed special characters."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com/page", custom_code="my-custom_code")

        assert shortener.exists("my-custom_code")

    def test_url_with_query_and_fragment(self):
        """Test URL with query parameters and fragment."""
        shortener = URLShortener()
        url = "https://example.com/page?param1=value1&param2=value2#section"

        code = shortener.shorten(url)
        resolved = shortener.resolve(code)

        assert resolved == url