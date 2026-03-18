"""
Tests for the main URLShortener API facade.
"""
import pytest
from datetime import datetime, date, timedelta

from pyshort.api import (
    URLShortener,
    URLShortenerError,
    InvalidURLOrCodeError,
    CodeAlreadyExistsError,
    ResolveError,
    StatisticsError,
)
from pyshort.storage import DictStorage, NotFoundError
from pyshort.validator import URLValidator, BlockedDomainError
from pyshort.stats import StatisticsTracker
from pyshort.models import ShortURL


class TestURLShortenerInit:
    """Tests for URLShortener initialization."""

    def test_default_initialization(self):
        """Test initialization with default components."""
        shortener = URLShortener()
        assert isinstance(shortener._storage, DictStorage)
        assert isinstance(shortener._validator, URLValidator)
        assert isinstance(shortener._stats, StatisticsTracker)
        assert shortener._default_code_length == 6
        assert shortener._custom_code_min_length == 1
        assert shortener._custom_code_max_length == 32

    def test_custom_initialization(self):
        """Test initialization with custom components."""
        storage = DictStorage()
        validator = URLValidator(blocked_domains={"blocked.com"})
        stats = StatisticsTracker()

        shortener = URLShortener(
            storage=storage,
            validator=validator,
            stats=stats,
            default_code_length=8,
            custom_code_min_length=2,
            custom_code_max_length=16,
        )

        assert shortener._storage is storage
        assert shortener._validator is validator
        assert shortener._stats is stats
        assert shortener._default_code_length == 8
        assert shortener._custom_code_min_length == 2
        assert shortener._custom_code_max_length == 16

    def test_invalid_default_code_length(self):
        """Test initialization with invalid default code length."""
        with pytest.raises(ValueError, match="default_code_length must be between 1 and 32"):
            URLShortener(default_code_length=0)

        with pytest.raises(ValueError, match="default_code_length must be between 1 and 32"):
            URLShortener(default_code_length=33)

    def test_invalid_custom_code_length(self):
        """Test initialization with invalid custom code length constraints."""
        with pytest.raises(ValueError, match="custom_code_min_length must be at least 1"):
            URLShortener(custom_code_min_length=0)

        with pytest.raises(ValueError, match="custom_code_max_length must be >= custom_code_min_length"):
            URLShortener(custom_code_min_length=10, custom_code_max_length=5)


class TestShorten:
    """Tests for the shorten() method."""

    def test_shorten_with_random_code(self):
        """Test shortening a URL with a random generated code."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        assert code is not None
        assert isinstance(code, str)
        assert len(code) == 6  # Default length
        assert shortener._storage.exists(code)

    def test_shorten_with_custom_code(self):
        """Test shortening a URL with a custom code."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com", custom_code="mylink")

        assert code == "mylink"
        assert shortener._storage.exists("mylink")

    def test_shorten_normalizes_url(self):
        """Test that URLs are normalized when shortened."""
        shortener = URLShortener()
        code1 = shortener.shorten("HTTP://EXAMPLE.COM/path/")
        code2 = shortener.shorten("https://example.com/path")

        # Both should produce the same short code (same normalized URL)
        # Note: This might not happen if random codes are used, so let's check storage
        url1 = shortener._storage.get_by_code(code1)
        url2 = shortener._storage.get_by_code(code2)

        if code1 == code2:
            # Same code means URL was deduplicated (future enhancement)
            assert url1.original_url == url2.original_url
        else:
            # Different codes but normalized URLs should match
            assert url1.original_url == url2.original_url

    def test_shorten_invalid_url(self):
        """Test shortening an invalid URL."""
        shortener = URLShortener()

        with pytest.raises(InvalidURLOrCodeError, match="Invalid URL"):
            shortener.shorten("not-a-url")

        with pytest.raises(InvalidURLOrCodeError, match="Invalid URL"):
            shortener.shorten("ftp://example.com")

    def test_shorten_blocked_domain(self):
        """Test shortening a URL with a blocked domain."""
        validator = URLValidator(blocked_domains={"spam.com"})
        shortener = URLShortener(validator=validator)

        with pytest.raises(InvalidURLOrCodeError, match="Invalid URL"):
            shortener.shorten("https://spam.com")

    def test_shorten_invalid_custom_code(self):
        """Test shortening with an invalid custom code format."""
        shortener = URLShortener()

        # Custom code with invalid characters
        with pytest.raises(InvalidURLOrCodeError, match="Invalid custom code"):
            shortener.shorten("https://example.com", custom_code="code with spaces")

        # Custom code too short
        with pytest.raises(InvalidURLOrCodeError, match="Invalid custom code"):
            shortener.shorten("https://example.com", custom_code="")

    def test_shorten_duplicate_custom_code(self):
        """Test that duplicate custom codes are rejected."""
        shortener = URLShortener()
        shortener.shorten("https://example.com", custom_code="mylink")

        with pytest.raises(CodeAlreadyExistsError, match="already in use"):
            shortener.shorten("https://other.com", custom_code="mylink")

    def test_shorten_with_expiration(self):
        """Test shortening a URL with an expiration date."""
        shortener = URLShortener()
        future_date = (datetime.now() + timedelta(days=7)).isoformat()

        code = shortener.shorten("https://example.com", expires_at=future_date)
        short_url = shortener._storage.get_by_code(code)

        assert short_url.expires_at is not None
        assert not short_url.is_expired()

    def test_shorten_invalid_expiration_format(self):
        """Test shortening with an invalid expiration date format."""
        shortener = URLShortener()

        with pytest.raises(InvalidURLOrCodeError, match="Invalid expiration date format"):
            shortener.shorten("https://example.com", expires_at="not-a-date")

    def test_shorten_code_collision_handling(self):
        """Test that code collisions are handled (retries with different code)."""
        # This is difficult to test directly, but we can verify the mechanism exists
        shortener = URLShortener()
        # Generate multiple URLs - they should all get unique codes
        codes = set()
        for i in range(100):
            code = shortener.shorten(f"https://example{i}.com")
            codes.add(code)

        assert len(codes) == 100

    def test_shorten_preserves_url_components(self):
        """Test that URL components (query, fragment) are preserved."""
        shortener = URLShortener()
        url = "https://example.com/path?query=1&param=test#section"
        code = shortener.shorten(url)

        resolved = shortener.resolve(code, track_click=False)
        assert resolved == url


class TestResolve:
    """Tests for the resolve() method."""

    def test_resolve_existing_code(self):
        """Test resolving an existing short code."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        resolved_url = shortener.resolve(code)
        assert resolved_url == "https://example.com"

    def test_resolve_tracks_clicks(self):
        """Test that resolve tracks clicks by default."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        # Resolve once
        shortener.resolve(code)
        stats = shortener.get_stats(code)
        assert stats["click_count"] == 1

        # Resolve again
        shortener.resolve(code)
        stats = shortener.get_stats(code)
        assert stats["click_count"] == 2

    def test_resolve_without_tracking(self):
        """Test resolving without tracking clicks."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        shortener.resolve(code, track_click=False)
        stats = shortener.get_stats(code)
        assert stats["click_count"] == 0

    def test_resolve_nonexistent_code(self):
        """Test resolving a non-existent short code."""
        shortener = URLShortener()

        with pytest.raises(ResolveError, match="not found"):
            shortener.resolve("nonexistent")

    def test_resolve_empty_code(self):
        """Test resolving an empty short code."""
        shortener = URLShortener()

        with pytest.raises(ResolveError, match="must be a non-empty string"):
            shortener.resolve("")

    def test_resolve_expired_url(self):
        """Test resolving an expired URL."""
        shortener = URLShortener()
        past_date = (datetime.now() - timedelta(days=1)).isoformat()

        code = shortener.shorten("https://example.com", expires_at=past_date)

        with pytest.raises(ResolveError, match="has expired"):
            shortener.resolve(code, track_click=False)

    def test_resolve_preserves_original_url(self):
        """Test that resolve returns the exact original URL."""
        shortener = URLShortener()
        original = "https://example.com/path?query=value#anchor"
        code = shortener.shorten(original)

        resolved = shortener.resolve(code, track_click=False)
        assert resolved == original


class TestGetStats:
    """Tests for the get_stats() method."""

    def test_get_stats_existing_code(self):
        """Test getting statistics for an existing code."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        # Simulate some clicks
        shortener.resolve(code)
        shortener.resolve(code)

        stats = shortener.get_stats(code)
        assert stats["click_count"] == 2
        assert stats["original_url"] == "https://example.com"
        assert "created_at" in stats
        assert "is_expired" in stats
        assert isinstance(stats["is_expired"], bool)

    def test_get_stats_nonexistent_code(self):
        """Test getting statistics for a non-existent code."""
        shortener = URLShortener()

        with pytest.raises(StatisticsError, match="not found"):
            shortener.get_stats("nonexistent")

    def test_get_stats_empty_code(self):
        """Test getting statistics for an empty code."""
        shortener = URLShortener()

        with pytest.raises(StatisticsError, match="must be a non-empty string"):
            shortener.get_stats("")

    def test_get_stats_with_zero_clicks(self):
        """Test getting statistics for a URL with no clicks."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        stats = shortener.get_stats(code)
        assert stats["click_count"] == 0

    def test_get_stats_created_at_format(self):
        """Test that created_at is in ISO format."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        stats = shortener.get_stats(code)
        created_at_str = stats["created_at"]

        # Should be valid ISO format
        datetime.fromisoformat(created_at_str)


class TestDelete:
    """Tests for the delete() method."""

    def test_delete_existing_code(self):
        """Test deleting an existing short code."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        assert shortener._storage.exists(code)
        deleted = shortener.delete(code)
        assert deleted is True
        assert not shortener._storage.exists(code)

    def test_delete_nonexistent_code(self):
        """Test deleting a non-existent short code."""
        shortener = URLShortener()

        deleted = shortener.delete("nonexistent")
        assert deleted is False

    def test_delete_empty_code(self):
        """Test deleting with an empty code."""
        shortener = URLShortener()

        with pytest.raises(URLShortenerError, match="must be a non-empty string"):
            shortener.delete("")

    def test_delete_clears_statistics(self):
        """Test that deleting also clears statistics."""
        shortener = URLShortener()
        code = shortener.shorten("https://example.com")

        # Generate some clicks
        shortener.resolve(code)
        shortener.resolve(code)

        assert shortener._stats.get_click_stats(code) == 2

        # Delete the code
        shortener.delete(code)

        # Statistics should be reset
        assert shortener._stats.get_click_stats(code) == 0


class TestListAllURLs:
    """Tests for the list_all_urls() method."""

    def test_list_all_empty(self):
        """Test listing URLs when none exist."""
        shortener = URLShortener()
        urls = shortener.list_all_urls()

        assert urls == []

    def test_list_all_multiple_urls(self):
        """Test listing multiple URLs."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example1.com")
        code2 = shortener.shorten("https://example2.com")
        code3 = shortener.shorten("https://example3.com")

        urls = shortener.list_all_urls()

        assert len(urls) == 3

        # Check each URL has the right structure
        for url_info in urls:
            assert "short_code" in url_info
            assert "original_url" in url_info
            assert "click_count" in url_info
            assert "created_at" in url_info
            assert "is_expired" in url_info

    def test_list_all_includes_click_counts(self):
        """Test that list_all_urls includes click counts."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example1.com")
        code2 = shortener.shorten("https://example2.com")

        # Generate clicks
        shortener.resolve(code1)
        shortener.resolve(code1)
        shortener.resolve(code2)

        urls = shortener.list_all_urls()

        for url_info in urls:
            if url_info["short_code"] == code1:
                assert url_info["click_count"] == 2
            elif url_info["short_code"] == code2:
                assert url_info["click_count"] == 1


class TestGetTotalClicks:
    """Tests for the get_total_clicks() method."""

    def test_get_total_clicks_empty(self):
        """Test total clicks with no URLs."""
        shortener = URLShortener()
        assert shortener.get_total_clicks() == 0

    def test_get_total_clicks_multiple_urls(self):
        """Test total clicks across multiple URLs."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example1.com")
        code2 = shortener.shorten("https://example2.com")

        shortener.resolve(code1)
        shortener.resolve(code1)
        shortener.resolve(code1)
        shortener.resolve(code2)

        assert shortener.get_total_clicks() == 4


class TestGetStatsSummary:
    """Tests for the get_stats_summary() method."""

    def test_get_stats_summary_empty(self):
        """Test stats summary with no URLs."""
        shortener = URLShortener()
        summary = shortener.get_stats_summary()

        assert "total_clicks" in summary
        assert "total_urls" in summary
        assert "total_days" in summary
        assert "top_urls" in summary
        assert "today_clicks" in summary

        assert summary["total_urls"] == 0
        assert summary["total_clicks"] == 0

    def test_get_stats_summary_with_data(self):
        """Test stats summary with URL data."""
        shortener = URLShortener()
        code1 = shortener.shorten("https://example1.com")
        code2 = shortener.shorten("https://example2.com")

        shortener.resolve(code1)
        shortener.resolve(code1)
        shortener.resolve(code2)

        summary = shortener.get_stats_summary()

        assert summary["total_urls"] == 2
        assert summary["total_clicks"] == 3
        assert summary["total_days"] >= 1
        assert len(summary["top_urls"]) <= 5
        assert summary["today_clicks"] == 3


class TestGetterMethods:
    """Tests for component getter methods."""

    def test_get_storage(self):
        """Test getting the storage backend."""
        storage = DictStorage()
        shortener = URLShortener(storage=storage)

        assert shortener.get_storage() is storage

    def test_get_validator(self):
        """Test getting the validator."""
        validator = URLValidator()
        shortener = URLShortener(validator=validator)

        assert shortener.get_validator() is validator

    def test_get_stats_tracker(self):
        """Test getting the stats tracker."""
        stats = StatisticsTracker()
        shortener = URLShortener(stats=stats)

        assert shortener.get_stats_tracker() is stats


class TestRepr:
    """Tests for the __repr__ method."""

    def test_repr(self):
        """Test the string representation."""
        shortener = URLShortener()
        shortener.shorten("https://example.com")
        shortener.resolve("code")  # This will fail, but we just want to test repr

        repr_str = repr(shortener)
        assert "URLShortener" in repr_str
        assert "storage=" in repr_str
        assert "urls=" in repr_str
        assert "total_clicks=" in repr_str


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_complete_workflow(self):
        """Test a complete workflow: shorten, resolve, get stats, delete."""
        shortener = URLShortener()

        # Create a shortened URL
        code = shortener.shorten("https://example.com", custom_code="test")
        assert code == "test"

        # Resolve it
        url = shortener.resolve(code)
        assert url == "https://example.com"

        # Get stats
        stats = shortener.get_stats(code)
        assert stats["click_count"] == 1

        # Resolve again
        shortener.resolve(code)
        stats = shortener.get_stats(code)
        assert stats["click_count"] == 2

        # Delete it
        deleted = shortener.delete(code)
        assert deleted is True

        # Verify it's gone
        with pytest.raises(ResolveError):
            shortener.resolve(code)

    def test_multiple_urls_workflow(self):
        """Test workflow with multiple URLs."""
        shortener = URLShortener()

        urls = [
            ("https://site1.com", "link1"),
            ("https://site2.com", "link2"),
            ("https://site3.com", "link3"),
        ]

        # Create all URLs
        for url, code in urls:
            shortener.shorten(url, custom_code=code)

        # Resolve each
        for url, code in urls:
            resolved = shortener.resolve(code)
            assert resolved == url

        # Get all URLs
        all_urls = shortener.list_all_urls()
        assert len(all_urls) == 3

        # Get summary
        summary = shortener.get_stats_summary()
        assert summary["total_urls"] == 3
        assert summary["total_clicks"] == 3

    def test_concurrent_operations(self):
        """Test that operations work correctly in sequence (basic concurrency test)."""
        shortener = URLShortener()

        # Create multiple URLs
        codes = []
        for i in range(10):
            code = shortener.shorten(f"https://site{i}.com")
            codes.append(code)

        # Resolve all URLs
        for i, code in enumerate(codes):
            url = shortener.resolve(code)
            assert url == f"https://site{i}.com"

        # Get stats for all
        total = 0
        for code in codes:
            stats = shortener.get_stats(code)
            total += stats["click_count"]

        assert total == 10

        # Delete all
        deleted_count = 0
        for code in codes:
            if shortener.delete(code):
                deleted_count += 1

        assert deleted_count == 10

        # Verify all are gone
        all_urls = shortener.list_all_urls()
        assert len(all_urls) == 0