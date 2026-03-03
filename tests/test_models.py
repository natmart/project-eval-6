"""
Tests for the ShortURL data model.
"""
from datetime import datetime, timedelta
import pytest

from pyshort.models import ShortURL, InvalidURLError


class TestShortURLInitialization:
    """Tests for ShortURL initialization and URL validation."""

    def test_initialization_with_valid_url(self):
        """Test successful initialization with a valid HTTPS URL."""
        url = ShortURL(
            original_url="https://example.com", short_code="abc123"
        )
        assert url.original_url == "https://example.com"
        assert url.short_code == "abc123"
        assert url.click_count == 0
        assert url.expires_at is None
        assert isinstance(url.created_at, datetime)

    def test_initialization_with_http_url(self):
        """Test successful initialization with a valid HTTP URL."""
        url = ShortURL(
            original_url="http://example.com/path?query=1", short_code="def456"
        )
        assert url.original_url == "http://example.com/path?query=1"
        assert url.short_code == "def456"

    def test_initialization_with_invalid_url_no_scheme(self):
        """Test that initialization fails when URL has no scheme."""
        with pytest.raises(InvalidURLError) as exc_info:
            ShortURL(original_url="example.com", short_code="abc123")
        assert "scheme" in str(exc_info.value).lower()

    def test_initialization_with_invalid_scheme(self):
        """Test that initialization fails when URL has invalid scheme."""
        with pytest.raises(InvalidURLError) as exc_info:
            ShortURL(original_url="ftp://example.com", short_code="abc123")
        assert "http or https" in str(exc_info.value).lower()

    def test_initialization_with_invalid_url_no_netloc(self):
        """Test that initialization fails when URL has no network location."""
        with pytest.raises(InvalidURLError) as exc_info:
            ShortURL(original_url="https://", short_code="abc123")
        assert "network location" in str(exc_info.value).lower()

    def test_initialization_with_empty_url(self):
        """Test that initialization fails with empty URL."""
        with pytest.raises(InvalidURLError) as exc_info:
            ShortURL(original_url="", short_code="abc123")
        assert "non-empty" in str(exc_info.value).lower()

    def test_initialization_with_non_string_url(self):
        """Test that initialization fails with non-string URL."""
        with pytest.raises(InvalidURLError) as exc_info:
            ShortURL(original_url=12345, short_code="abc123")
        assert "non-empty string" in str(exc_info.value).lower()

    def test_initialization_with_negative_click_count(self):
        """Test that initialization fails with negative click_count."""
        with pytest.raises(ValueError) as exc_info:
            ShortURL(
                original_url="https://example.com",
                short_code="abc123",
                click_count=-1,
            )
        assert "non-negative" in str(exc_info.value).lower()

    def test_initialization_with_custom_datetime(self):
        """Test initialization with a custom created_at datetime."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        url = ShortURL(
            original_url="https://example.com",
            short_code="abc123",
            created_at=custom_time,
        )
        assert url.created_at == custom_time


class TestShortURLFields:
    """Tests for ShortURL field types and properties."""

    def test_original_url_is_string(self):
        """Test that original_url is always a string."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        assert isinstance(url.original_url, str)

    def test_short_code_is_string(self):
        """Test that short_code is always a string."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        assert isinstance(url.short_code, str)

    def test_click_count_is_integer(self):
        """Test that click_count is always an integer."""
        url = ShortURL(
            original_url="https://example.com", short_code="abc123", click_count=5
        )
        assert isinstance(url.click_count, int)

    def test_created_at_is_datetime(self):
        """Test that created_at is always a datetime object."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        assert isinstance(url.created_at, datetime)

    def test_expires_at_is_datetime_or_none(self):
        """Test that expires_at is either datetime or None."""
        url1 = ShortURL(original_url="https://example.com", short_code="abc123")
        assert url1.expires_at is None

        expiry = datetime(2024, 12, 31)
        url2 = ShortURL(
            original_url="https://example.com",
            short_code="abc123",
            expires_at=expiry,
        )
        assert url2.expires_at == expiry
        assert isinstance(url2.expires_at, datetime)


class TestShortURLDatetimeHandling:
    """Tests for datetime handling in ShortURL."""

    def test_created_at_defaults_to_current_time(self):
        """Test that created_at defaults to current UTC time."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        now = datetime.utcnow()
        # Should be within 1 second of current time
        assert abs((now - url.created_at).total_seconds()) < 1

    def test_created_at_uses_provided_datetime(self):
        """Test that created_at uses the provided datetime."""
        custom_time = datetime(2023, 6, 15, 14, 30, 45)
        url = ShortURL(
            original_url="https://example.com",
            short_code="abc123",
            created_at=custom_time,
        )
        assert url.created_at == custom_time

    def test_is_expired_with_no_expiry(self):
        """Test that expired check returns False when no expiry is set."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        assert url.is_expired() is False

    def test_is_expired_with_future_expiry(self):
        """Test that expired check returns False for future expiry."""
        future = datetime.utcnow() + timedelta(days=7)
        url = ShortURL(
            original_url="https://example.com",
            short_code="abc123",
            expires_at=future,
        )
        assert url.is_expired() is False

    def test_is_expired_with_past_expiry(self):
        """Test that expired check returns True for past expiry."""
        past = datetime.utcnow() - timedelta(days=7)
        url = ShortURL(
            original_url="https://example.com", short_code="abc123", expires_at=past
        )
        assert url.is_expired() is True

    def test_is_expired_with_exactly_now(self):
        """Test that expired check returns True when expiry is exactly now."""
        # Use a time slightly in the past to ensure it's considered expired
        now = datetime.utcnow() - timedelta(seconds=1)
        url = ShortURL(
            original_url="https://example.com", short_code="abc123", expires_at=now
        )
        assert url.is_expired() is True


class TestShortURLClickCount:
    """Tests for click_count functionality."""

    def test_initial_click_count_defaults_to_zero(self):
        """Test that click_count defaults to 0."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        assert url.click_count == 0

    def test_click_count_can_be_initialized(self):
        """Test that click_count can be initialized to a positive value."""
        url = ShortURL(
            original_url="https://example.com", short_code="abc123", click_count=10
        )
        assert url.click_count == 10

    def test_increment_clicks_by_one(self):
        """Test incrementing clicks by default (1)."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        new_count = url.increment_clicks()
        assert url.click_count == 1
        assert new_count == 1

    def test_increment_clicks_by_custom_value(self):
        """Test incrementing clicks by a custom value."""
        url = ShortURL(
            original_url="https://example.com", short_code="abc123", click_count=5
        )
        new_count = url.increment_clicks(3)
        assert url.click_count == 8
        assert new_count == 8

    def test_increment_clicks_multiple_times(self):
        """Test multiple increments."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        url.increment_clicks(2)
        url.increment_clicks(3)
        url.increment_clicks(1)
        assert url.click_count == 6

    def test_increment_clicks_with_zero(self):
        """Test incrementing clicks by zero."""
        url = ShortURL(
            original_url="https://example.com", short_code="abc123", click_count=5
        )
        new_count = url.increment_clicks(0)
        assert url.click_count == 5
        assert new_count == 5

    def test_increment_clicks_with_negative_value(self):
        """Test that incrementing with negative value raises ValueError."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        with pytest.raises(ValueError) as exc_info:
            url.increment_clicks(-1)
        assert "non-negative" in str(exc_info.value).lower()

    def test_increment_clicks_returns_new_count(self):
        """Test that increment_clicks returns the new count."""
        url = ShortURL(
            original_url="https://example.com", short_code="abc123", click_count=7
        )
        new_count = url.increment_clicks(5)
        assert new_count == 12


class TestShortURLRepresentation:
    """Tests for __repr__ and __str__ methods."""

    def test_repr_includes_all_fields(self):
        """Test that __repr__ includes all relevant fields."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        expiry = datetime(2024, 12, 31, 23, 59, 59)
        url = ShortURL(
            original_url="https://example.com",
            short_code="abc123",
            created_at=custom_time,
            click_count=5,
            expires_at=expiry,
        )
        repr_str = repr(url)

        assert "ShortURL" in repr_str
        assert "original_url='https://example.com'" in repr_str
        assert "short_code='abc123'" in repr_str
        assert "created_at='2023-01-01T12:00:00'" in repr_str
        assert "click_count=5" in repr_str
        assert "expires_at='2024-12-31T23:59:59'" in repr_str

    def test_repr_with_none_expires_at(self):
        """Test that __repr__ shows None when expires_at is None."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        repr_str = repr(url)
        assert "expires_at=None" in repr_str

    def test_str_returns_simple_representation(self):
        """Test that __str__ returns a simple, user-friendly representation."""
        url = ShortURL(original_url="https://example.com", short_code="abc123")
        str_repr = str(url)
        assert str_repr == "abc123 -> https://example.com"

    def test_repr_format_with_complex_url(self):
        """Test __repr__ with a complex URL containing query parameters."""
        url = ShortURL(
            original_url="https://example.com/path?foo=bar&baz=qux",
            short_code="xyz789",
        )
        repr_str = repr(url)
        assert "original_url='https://example.com/path?foo=bar&baz=qux'" in repr_str
        assert "short_code='xyz789'" in repr_str


class TestShortURLValidationEdgeCases:
    """Tests for edge cases in URL validation."""

    def test_url_with_trailing_spaces_is_normalized(self):
        """Test that URLs with trailing spaces are normalized."""
        url = ShortURL(
            original_url="  https://example.com  ", short_code="abc123"
        )
        assert url.original_url == "https://example.com"

    def test_url_with_leading_spaces_is_normalized(self):
        """Test that URLs with leading spaces are normalized."""
        url = ShortURL(
            original_url="   https://example.com/path", short_code="abc123"
        )
        assert url.original_url == "https://example.com/path"

    def test_url_with_port(self):
        """Test that URLs with custom ports are accepted."""
        url = ShortURL(
            original_url="https://example.com:8443/path", short_code="abc123"
        )
        assert url.original_url == "https://example.com:8443/path"

    def test_url_with_fragment(self):
        """Test that URLs with fragments are accepted."""
        url = ShortURL(
            original_url="https://example.com/page#section", short_code="abc123"
        )
        assert url.original_url == "https://example.com/page#section"

    def test_url_with_auth(self):
        """Test that URLs with authentication are accepted."""
        url = ShortURL(
            original_url="https://user:pass@example.com", short_code="abc123"
        )
        assert url.original_url == "https://user:pass@example.com"

    def test_localhost_url(self):
        """Test that localhost URLs are accepted."""
        url = ShortURL(
            original_url="http://localhost:8000", short_code="abc123"
        )
        assert url.original_url == "http://localhost:8000"

    def test_ip_address_url(self):
        """Test that IP address URLs are accepted."""
        url = ShortURL(
            original_url="https://192.168.1.1/api", short_code="abc123"
        )
        assert url.original_url == "https://192.168.1.1/api"