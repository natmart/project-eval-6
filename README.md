# pyshort - Python URL Shortener v3

A simple and efficient Python URL shortener library.

## Features

- Simple and intuitive API
- Efficient URL shortening and resolution
- Customizable short codes
- Persistent storage support
- RESTful API for web integration

## Installation

```bash
pip install pyshort
```

## Quick Start

```python
from pyshort import URLShortener

# Create a shortener instance
shortener = URLShortener()

# Shorten a URL
short_url = shortener.shorten("https://example.com/very/long/url")
print(f"Shortened URL: {short_url}")

# Resolve a short URL
original_url = shortener.resolve(short_url)
print(f"Original URL: {original_url}")
```

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/yourusername/pyshort.git
cd pyshort

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=pyshort --cov-report=html
```

### Code formatting and linting

```bash
# Format code with black
black pyshort tests

# Lint with flake8
flake8 pyshort tests

# Type check with mypy
mypy pyshort
```

## Requirements

- Python 3.8 or higher
- pytest 7.0.0 or higher (for development)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

- [x] Project structure initialization
- [ ] Core URL shortening functionality
- [ ] Storage backends (memory, SQLite, Redis)
- [ ] REST API implementation
- [ ] CLI interface
- [ ] Analytics and statistics
- [ ] Rate limiting and security features