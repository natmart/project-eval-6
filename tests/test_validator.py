"""
Comprehensive tests for the URL validator module.
"""

import pytest

from pyshort.validator import (
    BlockedDomainError,
    DEFAULT_BLOCKED_DOMAINS,
    InvalidDomainError,
    InvalidSchemeError,
    URLValidator,
    ValidationError,
    is_domain_blocked,
    normalize_url,
    validate_domain_format,
    validate_scheme,
    validate_url,
)


class TestValidateScheme:
    """Tests for validate_scheme function."""

    def test_valid_http_scheme(self):
        """Test that HTTP scheme is accepted."""
        assert validate_scheme("http://example.com") == "http://example.com"
        assert validate_scheme("HTTP://example.com") == "HTTP://example.com"

    def test_valid_https_scheme(self):
        """Test that HTTPS scheme is accepted."""
        assert validate_scheme("https://example.com") == "https://example.com"
        assert validate_scheme("HTTPS://example.com") == "HTTPS://example.com"

    def test_missing_scheme(self):
        """Test that missing scheme raises InvalidSchemeError."""
        with pytest.raises(InvalidSchemeError) as exc_info:
            validate_scheme("example.com")
        assert "must include a scheme" in str(exc_info.value)

    def test_invalid_scheme(self):
        """Test that schemes other than http/https are rejected."""
        invalid_schemes = [
            "ftp://example.com",
            "mailto://example.com",
            "file://example.com",
            "ssh://example.com",
        ]
        for url in invalid_schemes:
            with pytest.raises(InvalidSchemeError) as exc_info:
                validate_scheme(url)
            assert "must be http or https" in str(exc_info.value)

    def test_empty_url(self):
        """Test that empty URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_scheme("")
        assert "must be a non-empty string" in str(exc_info.value)

    def test_non_string_input(self):
        """Test that non-string input raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_scheme(None)
        assert "must be a non-empty string" in str(exc_info.value)

        with pytest.raises(ValidationError):
            validate_scheme(123)

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        assert validate_scheme("  http://example.com  ") == "  http://example.com  "


class TestValidateDomainFormat:
    """Tests for validate_domain_format function."""

    def test_valid_simple_domain(self):
        """Test that simple valid domains are accepted."""
        assert validate_domain_format("http://example.com") == "http://example.com"
        assert validate_domain_format("https://sub.example.com") == "https://sub.example.com"

    def test_valid_subdomain(self):
        """Test that subdomains are accepted."""
        assert validate_domain_format("http://www.example.com") == "http://www.example.com"
        assert validate_domain_format("http://api.service.example.com") == "http://api.service.example.com"

    def test_valid_domain_with_port(self):
        """Test that domains with ports are accepted."""
        assert validate_domain_format("http://example.com:8080") == "http://example.com:8080"
        assert validate_domain_format("https://example.com:443") == "https://example.com:443"

    def test_valid_localhost(self):
        """Test that localhost is accepted."""
        assert validate_domain_format("http://localhost") == "http://localhost"
        assert validate_domain_format("http://localhost:8000") == "http://localhost:8000"

    def test_valid_ipv4(self):
        """Test that valid IPv4 addresses are accepted."""
        assert validate_domain_format("http://192.168.1.1") == "http://192.168.1.1"
        assert validate_domain_format("http://10.0.0.1:8080") == "http://10.0.0.1:8080"

    def test_valid_ipv6(self):
        """Test that IPv6 addresses are accepted."""
        assert validate_domain_format("http://[::1]") == "http://[::1]"
        assert validate_domain_format("http://[2001:db8::1]") == "http://[2001:db8::1]"

    def test_missing_netloc(self):
        """Test that missing netloc raises InvalidDomainError."""
        with pytest.raises(InvalidDomainError) as exc_info:
            validate_domain_format("http://")
        assert "must include a domain" in str(exc_info.value)

    def test_invalid_domain_single_label(self):
        """Test that single-label domains are rejected."""
        with pytest.raises(InvalidDomainError) as exc_info:
            validate_domain_format("http://example")
        assert "must have at least two labels" in str(exc_info.value)

    def test_invalid_domain_empty_label(self):
        """Test that domains with empty labels are rejected."""
        with pytest.raises(InvalidDomainError) as exc_info:
            validate_domain_format("http://example..com")
        assert "cannot be empty" in str(exc_info.value)

        with pytest.raises(InvalidDomainError):
            validate_domain_format("http://.example.com")

    def test_invalid_domain_label_too_long(self):
        """Test that labels exceeding 63 characters are rejected."""
        long_label = "a" * 64
        with pytest.raises(InvalidDomainError) as exc_info:
            validate_domain_format(f"http://{long_label}.com")
        assert "cannot exceed 63 characters" in str(exc_info.value)

    def test_invalid_domain_label_starts_with_hyphen(self):
        """Test that labels starting with hyphen are rejected."""
        with pytest.raises(InvalidDomainError):
            validate_domain_format("http://-example.com")

    def test_invalid_domain_label_ends_with_hyphen(self):
        """Test that labels ending with hyphen are rejected."""
        with pytest.raises(InvalidDomainError):
            validate_domain_format("http://example-.com")

    def test_invalid_domain_tld_starts_with_hyphen(self):
        """Test that TLD starting with hyphen is rejected."""
        with pytest.raises(InvalidDomainError) as exc_info:
            validate_domain_format("http://example.-com")
        assert "TLD cannot start or end with hyphen" in str(exc_info.value)

    def test_invalid_domain_tld_ends_with_hyphen(self):
        """Test that TLD ending with hyphen is rejected."""
        with pytest.raises(InvalidDomainError) as exc_info:
            validate_domain_format("http://example.com-")
        assert "TLD cannot start or end with hyphen" in str(exc_info.value)

    def test_invalid_domain_invalid_characters(self):
        """Test that domains with invalid characters are rejected."""
        with pytest.raises(InvalidDomainError):
            validate_domain_format("http://example_com.com")

        with pytest.raises(InvalidDomainError):
            validate_domain_format("http://example!.com")

    def test_invalid_ipv4_octets(self):
        """Test that invalid IPv4 octets are rejected."""
        # Octets > 255
        with pytest.raises(InvalidDomainError):
            validate_domain_format("http://256.1.1.1")

        with pytest.raises(InvalidDomainError):
            validate_domain_format("http://192.168.1.300")

    def test_empty_url(self):
        """Test that empty URL raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_domain_format("")

    def test_non_string_input(self):
        """Test that non-string input raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_domain_format(None)


class TestIsDomainBlocked:
    """Tests for is_domain_blocked function."""

    def test_not_blocked(self):
        """Test that non-blocked domains return False."""
        assert is_domain_blocked("http://example.com") is False
        assert is_domain_blocked("http://sub.example.com") is False

    def test_exact_match_blocked(self):
        """Test that exact domain matches are blocked."""
        assert is_domain_blocked("http://malicious.example.com") is True
        assert is_domain_blocked("https://spam.example.com") is True

    def test_subdomain_blocked(self):
        """Test that subdomains of blocked domains are blocked."""
        blocked = {"example.com"}
        assert is_domain_blocked("http://sub.example.com", blocked) is True
        assert is_domain_blocked("http://deep.sub.example.com", blocked) is True

    def test_case_insensitive(self):
        """Test that blocking is case-insensitive."""
        blocked = {"Example.Com"}
        assert is_domain_blocked("http://example.com", blocked) is True
        assert is_domain_blocked("http://EXAMPLE.COM", blocked) is True

    def test_with_port(self):
        """Test that ports are ignored when checking blocked domains."""
        blocked = {"example.com"}
        assert is_domain_blocked("http://example.com:8080", blocked) is True

    def test_empty_blocked_list(self):
        """Test that no domains are blocked with empty list."""
        assert is_domain_blocked("http://example.com", set()) is False

    def test_default_blocked_domains(self):
        """Test that default blocked domains work."""
        assert is_domain_blocked("http://malicious.example.com", DEFAULT_BLOCKED_DOMAINS) is True
        assert is_domain_blocked("http://example.com", DEFAULT_BLOCKED_DOMAINS) is False

    def test_empty_url(self):
        """Test that empty URL returns False."""
        assert is_domain_blocked("") is False

    def test_non_string_input(self):
        """Test that non-string input returns False."""
        assert is_domain_blocked(None) is False


class TestNormalizeUrl:
    """Tests for normalize_url function."""

    def test_lower_case_scheme(self):
        """Test that scheme is lowercased."""
        assert normalize_url("HTTP://example.com") == "http://example.com"
        assert normalize_url("HTTPS://example.com") == "https://example.com"
        assert normalize_url("HtTp://example.com") == "http://example.com"

    def test_lower_case_domain(self):
        """Test that domain is lowercased."""
        assert normalize_url("http://EXAMPLE.COM") == "http://example.com"
        assert normalize_url("http://Example.Com") == "http://example.com"
        assert normalize_url("https://WWW.EXAMPLE.COM") == "https://www.example.com"

    def test_remove_trailing_slash(self):
        """Test that trailing slashes are removed from path."""
        assert normalize_url("http://example.com/") == "http://example.com"
        assert normalize_url("http://example.com/path/") == "http://example.com/path"
        assert normalize_url("http://example.com/path/to/page/") == "http://example.com/path/to/page"

    def test_preserve_root_slash(self):
        """Test that single slash at root is handled (removed)."""
        assert normalize_url("http://example.com/") == "http://example.com"

    def test_preserve_query_parameters(self):
        """Test that query parameters are preserved."""
        url = "http://example.com/path?query=1&param=2"
        assert normalize_url(url) == url

    def test_preserve_fragment(self):
        """Test that fragments are preserved."""
        url = "http://example.com/path#section"
        assert normalize_url(url) == url

    def test_preserve_query_and_fragment(self):
        """Test that both query and fragment are preserved."""
        url = "http://example.com/path?q=1#section"
        assert normalize_url(url) == url

    def test_whitespace_handling(self):
        """Test that whitespace is stripped."""
        assert normalize_url("  http://example.com  ") == "http://example.com"
        assert normalize_url("\nhttp://example.com\n") == "http://example.com"

    def test_url_without_path(self):
        """Test normalization of URL without path."""
        assert normalize_url("http://example.com") == "http://example.com"

    def test_mixed_case_normalization(self):
        """Test comprehensive mixed case normalization."""
        url = normalize_url("HTTP://WWW.EXAMPLE.COM/PATH/?Q=1#SECTION")
        assert url == "http://www.example.com/PATH?Q=1#SECTION"

    def test_empty_url(self):
        """Test that empty URL raises ValidationError."""
        with pytest.raises(ValidationError):
            normalize_url("")

    def test_non_string_input(self):
        """Test that non-string input raises ValidationError."""
        with pytest.raises(ValidationError):
            normalize_url(None)


class TestValidateUrl:
    """Tests for validate_url function."""

    def test_valid_url_normalized(self):
        """Test that valid URLs are validated and normalized by default."""
        result = validate_url("HTTP://EXAMPLE.COM/PATH/")
        assert result == "http://example.com/path"

    def test_valid_url_not_normalized(self):
        """Test that valid URLs can be validated without normalization."""
        url = "HTTP://EXAMPLE.COM/PATH/"
        result = validate_url(url, normalize=False)
        assert result == url

    def test_invalid_scheme(self):
        """Test that invalid scheme raises InvalidSchemeError."""
        with pytest.raises(InvalidSchemeError):
            validate_url("ftp://example.com")

    def test_invalid_domain(self):
        """Test that invalid domain raises InvalidDomainError."""
        with pytest.raises(InvalidDomainError):
            validate_url("http://example")

    def test_blocked_domain(self):
        """Test that blocked domains raise BlockedDomainError."""
        with pytest.raises(BlockedDomainError) as exc_info:
            validate_url("http://malicious.example.com")
        assert "malicious.example.com" in str(exc_info.value)
        assert "is blocked" in str(exc_info.value)

    def test_custom_blocked_domains(self):
        """Test that custom blocked domains work."""
        blocked = {"example.com"}
        with pytest.raises(BlockedDomainError):
            validate_url("http://example.com", blocked)

    def test_passes_all_validations(self):
        """Test URL that passes all validations."""
        result = validate_url("https://sub.example.com/path?q=1")
        assert result == "https://sub.example.com/path?q=1"


class TestURLValidator:
    """Tests for URLValidator class."""

    def test_initialization_default(self):
        """Test default initialization."""
        validator = URLValidator()
        assert validator.blocked_domains == DEFAULT_BLOCKED_DOMAINS
        assert validator.normalize_by_default is True

    def test_initialization_custom_blocked(self):
        """Test initialization with custom blocked domains."""
        blocked = {"example.com", "spam.com"}
        validator = URLValidator(blocked_domains=blocked)
        assert validator.blocked_domains == blocked

    def test_initialization_normalize_false(self):
        """Test initialization with normalize_by_default=False."""
        validator = URLValidator(normalize_by_default=False)
        assert validator.normalize_by_default is False

    def test_validate_scheme_method(self):
        """Test validate_scheme method."""
        validator = URLValidator()
        assert validator.validate_scheme("http://example.com") == "http://example.com"

        with pytest.raises(InvalidSchemeError):
            validator.validate_scheme("ftp://example.com")

    def test_validate_domain_format_method(self):
        """Test validate_domain_format method."""
        validator = URLValidator()
        assert validator.validate_domain_format("http://example.com") == "http://example.com"

        with pytest.raises(InvalidDomainError):
            validator.validate_domain_format("http://example")

    def test_is_domain_blocked_method(self):
        """Test is_domain_blocked method."""
        validator = URLValidator(blocked_domains={"example.com"})
        assert validator.is_domain_blocked("http://example.com") is True
        assert validator.is_domain_blocked("http://other.com") is False

    def test_normalize_url_method(self):
        """Test normalize_url method."""
        validator = URLValidator()
        result = validator.normalize_url("HTTP://EXAMPLE.COM/")
        assert result == "http://example.com"

    def test_validate_url_method_with_defaults(self):
        """Test validate_url method with default settings."""
        validator = URLValidator()
        result = validator.validate_url("HTTP://EXAMPLE.COM/PATH/")
        assert result == "http://example.com/path"

    def test_validate_url_method_normalize_false(self):
        """Test validate_url method with normalize set to False."""
        validator = URLValidator()
        url = "HTTP://EXAMPLE.COM/PATH/"
        result = validator.validate_url(url, normalize=False)
        assert result == url

    def test_validate_url_method_uses_instance_normalize_default(self):
        """Test that validate_url uses instance normalize_by_default."""
        validator = URLValidator(normalize_by_default=False)
        url = "HTTP://EXAMPLE.COM/PATH/"
        result = validator.validate_url(url)
        assert result == url

    def test_validate_url_blocked_domain(self):
        """Test validate_url with blocked domain."""
        validator = URLValidator(blocked_domains={"example.com"})
        with pytest.raises(BlockedDomainError):
            validator.validate_url("http://example.com")

    def test_add_blocked_domain(self):
        """Test add_blocked_domain method."""
        validator = URLValidator()
        validator.add_blocked_domain("NEW-DOMAIN.COM")
        assert "new-domain.com" in validator.blocked_domains
        assert validator.is_domain_blocked("http://new-domain.com") is True

    def test_remove_blocked_domain(self):
        """Test remove_blocked_domain method."""
        validator = URLValidator(blocked_domains={"example.com"})
        validator.remove_blocked_domain("example.com")
        assert "example.com" not in validator.blocked_domains
        assert validator.is_domain_blocked("http://example.com") is False

    def test_remove_nonexistent_domain(self):
        """Test that removing non-existent domain doesn't raise error."""
        validator = URLValidator()
        # Should not raise
        validator.remove_blocked_domain("nonexistent.com")

    def test_get_blocked_domains(self):
        """Test get_blocked_domains returns a copy."""
        validator = URLValidator(blocked_domains={"example.com"})
        blocked = validator.get_blocked_domains()
        blocked.add("new.com")
        assert "new.com" not in validator.blocked_domains

    def test_set_blocked_domains(self):
        """Test set_blocked_domains method."""
        validator = URLValidator()
        validator.set_blocked_domains({"site1.com", "site2.com"})
        assert "site1.com" in validator.blocked_domains
        assert "site2.com" in validator.blocked_domains

    def test_set_blocked_domains_filters_empty(self):
        """Test that set_blocked_domains filters out empty strings."""
        validator = URLValidator()
        validator.set_blocked_domains({"example.com", "", "  ", "spam.com"})
        assert "example.com" in validator.blocked_domains
        assert "spam.com" in validator.blocked_domains
        assert "" not in validator.blocked_domains


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_long_domain(self):
        """Test that very long domain names are handled correctly."""
        # Create a domain with many valid labels
        labels = ["label" + str(i) for i in range(10)]
        domain = ".".join(labels) + ".com"
        result = validate_domain_format(f"http://{domain}")
        assert result == f"http://{domain}"

    def test_max_length_label(self):
        """Test that 63-character label is accepted."""
        label = "a" * 63
        result = validate_domain_format(f"http://{label}.com")
        assert result == f"http://{label}.com"

    def test_domain_with_digits(self):
        """Test that digits in domain are accepted."""
        assert validate_domain_format("http://example123.com") == "http://example123.com"
        assert validate_domain_format("http://123.example.com") == "http://123.example.com"

    def test_domain_with_hyphen_in_middle(self):
        """Test that hyphens in middle of label are accepted."""
        assert validate_domain_format("http://my-example.com") == "http://my-example.com"
        assert validate_domain_format("http://my-new-site.example.com") == "http://my-new-site.example.com"

    def test_url_with_username_password(self):
        """Test that URLs with username:password are accepted."""
        assert normalize_url("HTTP://USER:PASS@EXAMPLE.COM") == "http://user:pass@example.com"

    def test_url_with_path_and_multiple_slashes(self):
        """Test that paths with multiple slashes are handled."""
        result = normalize_url("http://example.com/path//to///page//")
        assert result == "http://example.com/path//to///page"

    def test_url_with_empty_query(self):
        """Test that URL with empty query is handled."""
        result = normalize_url("http://example.com/path?")
        assert result == "http://example.com/path"

    def test_url_with_empty_fragment(self):
        """Test that URL with empty fragment is handled."""
        result = normalize_url("http://example.com/path#")
        assert result == "http://example.com/path"

    def test_subdomain_of_blocked_domain(self):
        """Test that subdomains of blocked domains are caught."""
        validator = URLValidator(blocked_domains={"example.com"})
        with pytest.raises(BlockedDomainError):
            validator.validate_url("http://sub.example.com")

    def test_blocked_domain_with_port(self):
        """Test that blocked domain check works with port."""
        validator = URLValidator(blocked_domains={"example.com"})
        with pytest.raises(BlockedDomainError):
            validator.validate_url("http://example.com:8080")

    def test_mixed_case_blocked_domain(self):
        """Test that blocked domain check is case-insensitive."""
        validator = URLValidator(blocked_domains={"Example.Com"})
        with pytest.raises(BlockedDomainError):
            validator.validate_url("http://example.com")

        with pytest.raises(BlockedDomainError):
            validator.validate_url("http://EXAMPLE.COM")


class TestRealWorldUrls:
    """Tests with real-world URL examples."""

    def test_common_websites(self):
        """Test validation of common website URLs."""
        urls = [
            "https://www.google.com",
            "https://github.com/user/repo",
            "https://stackoverflow.com/questions/123",
            "https://example.com/path/to/page?param=value",
        ]
        for url in urls:
            result = validate_url(url)
            assert result == url

    def test_url_with_special_characters_in_query(self):
        """Test URLs with special characters in query parameters."""
        url = "https://example.com/search?q=hello+world&lang=en"
        result = validate_url(url)
        assert result == url

    def test_url_with_encoded_characters(self):
        """Test URLs with URL-encoded characters."""
        url = "https://example.com/search?q=hello%20world"
        result = validate_url(url)
        assert result == url

    def test_api_endpoints(self):
        """Test API endpoint URLs."""
        urls = [
            "https://api.example.com/v1/users",
            "https://api.example.com/v1/users/123/posts",
            "https://api.example.com/v1/search?q=test",
        ]
        for url in urls:
            result = validate_url(url)
            assert result == url