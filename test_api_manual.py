#!/usr/bin/env python
"""Manual test script for the API module."""

# Add current directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("Testing imports...")
    from pyshort.api import URLShortener, URLShortenerError
    from pyshort.storage import DictStorage
    print("✓ Imports successful")

    print("\nTesting URLShortener initialization...")
    shortener = URLShortener()
    print("✓ Initialization successful")

    print("\nTesting shorten with random code...")
    code = shortener.shorten("https://example.com")
    print(f"✓ Shortened URL, code: {code}")

    print("\nTesting shorten with custom code...")
    custom_code = shortener.shorten("https://github.com", custom_code="github")
    print(f"✓ Shortened URL with custom code: {custom_code}")

    print("\nTesting resolve...")
    url = shortener.resolve(code)
    print(f"✓ Resolved code {code} to: {url}")
    assert url == "https://example.com"

    print("\nTesting get_stats...")
    stats = shortener.get_stats(code)
    print(f"✓ Stats: {stats}")
    assert stats["click_count"] >= 1

    print("\nTesting list_all_urls...")
    urls = shortener.list_all_urls()
    print(f"✓ Found {len(urls)} URLs")

    print("\nTesting resolve increments clicks...")
    shortener.resolve(code)
    stats = shortener.get_stats(code)
    print(f"✓ Click count after second resolve: {stats['click_count']}")

    print("\nTesting delete...")
    deleted = shortener.delete(code)
    print(f"✓ Deleted: {deleted}")
    assert deleted is True

    print("\nTesting resolve deleted code...")
    try:
        shortener.resolve(code)
        print("✗ Should have raised an error")
        sys.exit(1)
    except Exception as e:
        print(f"✓ Correctly raised error: {type(e).__name__}")

    print("\nTesting delete non-existent code...")
    deleted = shortener.delete("nonexistent")
    print(f"✓ Deleted non-existent code returns: {deleted}")
    assert deleted is False

    print("\nTesting error cases...")
    try:
        shortener.shorten("not-a-url")
        print("✗ Should have raised error for invalid URL")
        sys.exit(1)
    except Exception as e:
        print(f"✓ Invalid URL error: {type(e).__name__}")

    try:
        shortener.shorten("https://example.com", custom_code="github")
        print("✗ Should have raised error for duplicate code")
        sys.exit(1)
    except Exception as e:
        print(f"✓ Duplicate code error: {type(e).__name__}")

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)