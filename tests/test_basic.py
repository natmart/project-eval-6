"""
Basic tests to verify project setup
"""


def test_import():
    """Test that the pyshort package can be imported."""
    import pyshort

    assert pyshort is not None
    assert hasattr(pyshort, "__version__")


def test_version():
    """Test that the version is defined."""
    import pyshort

    assert pyshort.__version__ == "0.1.0"