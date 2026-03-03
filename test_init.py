#!/usr/bin/env python3
"""Test script to verify package initialization."""

def test_imports():
    """Test that the package imports correctly."""
    # Test version
    from pyshort import __version__
    assert __version__ == "0.1.0", f"Expected version 0.1.0, got {__version__}"
    print(f"✓ __version__ is defined: {__version__}")

    # Test author info
    from pyshort import __author__, __email__
    assert __author__ == "Your Name", f"Expected author 'Your Name', got {__author__}"
    assert __email__ == "your.email@example.com", f"Expected email 'your.email@example.com', got {__email__}"
    print(f"✓ __author__: {__author__}")
    print(f"✓ __email__: {__email__}")

    # Test model imports
    from pyshort import ShortURL, InvalidURLError
    assert ShortURL is not None, "ShortURL should be importable"
    assert InvalidURLError is not None, "InvalidURLError should be importable"
    print("✓ Models exported: ShortURL, InvalidURLError")

    # Test validator imports
    from pyshort import (
        URLValidator,
        ValidationError,
        InvalidSchemeError,
        InvalidDomainError,
        BlockedDomainError,
    )
    assert URLValidator is not None, "URLValidator should be importable"
    assert ValidationError is not None, "ValidationError should be importable"
    assert InvalidSchemeError is not None, "InvalidSchemeError should be importable"
    assert InvalidDomainError is not None, "InvalidDomainError should be importable"
    assert BlockedDomainError is not None, "BlockedDomainError should be importable"
    print("✓ Validator exported: URLValidator, ValidationError, etc.")

    # Test generator imports
    from pyshort import (
        generate_random_code,
        generate_custom_code,
        encode_base62,
        decode_base62,
        CodeGenerationError,
        InvalidCustomCodeError,
    )
    assert generate_random_code is not None, "generate_random_code should be importable"
    assert generate_custom_code is not None, "generate_custom_code should be importable"
    assert encode_base62 is not None, "encode_base62 should be importable"
    assert decode_base62 is not None, "decode_base62 should be importable"
    assert CodeGenerationError is not None, "CodeGenerationError should be importable"
    assert InvalidCustomCodeError is not None, "InvalidCustomCodeError should be importable"
    print("✓ Generator exported: generate_random_code, generate_custom_code, etc.")

    # Test storage imports
    from pyshort import (
        DictStorage,
        StorageBase,
        StorageError,
        DuplicateCodeError,
        NotFoundError,
    )
    assert DictStorage is not None, "DictStorage should be importable"
    assert StorageBase is not None, "StorageBase should be importable"
    assert StorageError is not None, "StorageError should be importable"
    assert DuplicateCodeError is not None, "DuplicateCodeError should be importable"
    assert NotFoundError is not None, "NotFoundError should be importable"
    print("✓ Storage exported: DictStorage, StorageBase, etc.")

    # Test statistics import
    from pyshort import StatisticsTracker
    assert StatisticsTracker is not None, "StatisticsTracker should be importable"
    print("✓ Statistics exported: StatisticsTracker")

    # Test __all__
    import pyshort
    assert hasattr(pyshort, '__all__'), "__all__ should be defined"
    assert len(pyshort.__all__) == 22, f"Expected 22 exports, got {len(pyshort.__all__)}"
    print(f"✓ __all__ contains {len(pyshort.__all__)} exports")

    print("\n✅ All package initialization tests passed!")

if __name__ == "__main__":
    test_imports()