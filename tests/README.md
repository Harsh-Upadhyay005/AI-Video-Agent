# Testing Guide

## Overview

This directory contains the test suite for the AI Video Agent application. Tests are written using pytest and organized by module.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Pytest configuration and fixtures
├── test_validators.py   # Input validation tests
├── test_config.py       # Configuration management tests
├── test_security.py     # Security utilities tests
├── test_api.py          # FastAPI endpoint tests
└── README.md            # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_validators.py
```

### Run specific test class
```bash
pytest tests/test_validators.py::TestURLValidation
```

### Run specific test function
```bash
pytest tests/test_validators.py::TestURLValidation::test_valid_youtube_urls
```

### Run tests with markers
```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

### Run with coverage
```bash
# Generate coverage report
pytest --cov=core --cov=api --cov-report=html

# View HTML coverage report
# Open htmlcov/index.html in your browser
```

### Run with verbose output
```bash
pytest -v -s
```

## Test Categories

### Unit Tests
Test individual components in isolation:
- Validators
- Configuration
- Security utilities
- Exception handling

### Integration Tests
Test interactions between components:
- API endpoints
- Database operations
- External API calls

### API Tests
Test FastAPI endpoints:
- Health checks
- Analysis endpoints
- Chat endpoints
- Error handling

## Writing Tests

### Example Test

```python
import pytest
from core.validators import InputValidator
from core.exceptions import ValidationError

def test_valid_url():
    """Test that valid URLs pass validation."""
    url = "https://www.youtube.com/watch?v=test"
    result = InputValidator.validate_url(url)
    assert result == url

def test_invalid_url():
    """Test that invalid URLs raise ValidationError."""
    with pytest.raises(ValidationError):
        InputValidator.validate_url("not_a_url")
```

### Using Fixtures

```python
def test_with_fixture(sample_transcript):
    """Test using a fixture."""
    assert len(sample_transcript) > 0
```

### Parametrized Tests

```python
@pytest.mark.parametrize("url,expected", [
    ("https://youtube.com/watch?v=1", "https://youtube.com/watch?v=1"),
    ("https://youtu.be/1", "https://youtu.be/1"),
])
def test_youtube_urls(url, expected):
    result = InputValidator.validate_url(url)
    assert result == expected
```

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **One Assertion**: Each test should ideally test one thing
3. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification
4. **Fixtures**: Use fixtures for common test data and setup
5. **Mocking**: Mock external dependencies (APIs, databases, etc.)
6. **Coverage**: Aim for high code coverage but focus on meaningful tests

## Continuous Integration

Tests run automatically on:
- Every commit
- Pull requests
- Before deployment

Minimum coverage requirement: 50%

## Troubleshooting

### Tests fail with import errors
- Ensure virtual environment is activated
- Install test dependencies: `pip install -r requirements.txt`

### Tests fail with missing environment variables
- Copy `.env.example` to `.env`
- Set required environment variables
- Tests use mock values from `conftest.py`

### Slow tests
- Use `-m "not slow"` to skip slow tests during development
- Full test suite runs in CI/CD

## Adding New Tests

1. Create a new test file in `tests/` directory
2. Import necessary modules and fixtures
3. Write test functions with `test_` prefix
4. Add appropriate markers (`@pytest.mark.unit`, etc.)
5. Run tests to verify they pass
6. Check coverage report to ensure new code is tested

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
