# Testing Guide

This directory contains the test suite for the Almacena Dashboard project.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_fetch_from_sheets.py
│   ├── test_data_pipeline.py
│   └── test_logger_config.py
├── integration/             # Integration tests (slower, external deps)
└── fixtures/                # Test data and mock files
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

This installs pytest and all testing tools:
- `pytest` - Test framework
- `pytest-cov` - Code coverage
- `pytest-mock` - Mocking utilities
- `pytest-env` - Environment variable management

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s
```

### Run Specific Test Categories

```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Run tests that require Google API
pytest -m google_api
```

### Run Specific Test Files

```bash
# Run tests for fetch_from_sheets module
pytest tests/unit/test_fetch_from_sheets.py

# Run tests for data pipeline
pytest tests/unit/test_data_pipeline.py

# Run tests for logging
pytest tests/unit/test_logger_config.py
```

### Run Specific Test Functions

```bash
# Run a specific test class
pytest tests/unit/test_data_pipeline.py::TestDataLoading

# Run a specific test function
pytest tests/unit/test_data_pipeline.py::TestDataLoading::test_load_data_csv_success
```

## Code Coverage

### Generate Coverage Report

```bash
# Run tests with coverage report
pytest --cov=scripts --cov=. --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=scripts --cov=. --cov-report=html

# Open HTML report
start htmlcov/index.html
```

### Coverage Goals

- **Overall**: Target 80%+ code coverage
- **Critical modules** (fetch_from_sheets, data_pipeline): 90%+
- **Utility modules**: 70%+

## Test Markers

Tests are categorized with markers for easy filtering:

- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Integration tests with external services
- `@pytest.mark.slow` - Tests that take >1 second
- `@pytest.mark.google_api` - Tests requiring Google API credentials

## Writing Tests

### Basic Test Structure

```python
import pytest

class TestMyFeature:
    """Tests for my feature."""

    @pytest.mark.unit
    def test_basic_functionality(self):
        """Test description."""
        # Arrange
        input_data = "test"

        # Act
        result = my_function(input_data)

        # Assert
        assert result == "expected"
```

### Using Fixtures

Fixtures are defined in `conftest.py` and can be used in any test:

```python
@pytest.mark.unit
def test_with_sample_data(sample_kpi_data):
    """Test using shared fixture."""
    assert len(sample_kpi_data) > 0
```

### Mocking External Services

```python
@pytest.mark.unit
def test_with_mock_api(mock_google_sheets_service):
    """Test with mocked Google Sheets API."""
    # Your test code here
    pass
```

### Testing Exceptions

```python
@pytest.mark.unit
def test_raises_error():
    """Test that error is raised."""
    with pytest.raises(ValueError, match="Expected error message"):
        my_function_that_raises()
```

## Common Testing Patterns

### Testing File Operations

```python
@pytest.mark.unit
def test_file_creation(tmp_path):
    """Test file creation using temporary directory."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    assert test_file.exists()
```

### Testing with Environment Variables

```python
@pytest.mark.unit
def test_with_env_var(monkeypatch):
    """Test with environment variable."""
    monkeypatch.setenv('MY_VAR', 'test_value')

    # Test code that uses MY_VAR
    pass
```

### Testing Logging

```python
@pytest.mark.unit
def test_logging(caplog):
    """Test that logging works."""
    with caplog.at_level(logging.INFO):
        my_function_that_logs()

    assert "Expected log message" in caplog.text
```

## Continuous Integration

Tests run automatically on:
- Every commit (local pre-commit hook - if configured)
- Every push to GitHub (GitHub Actions - if configured)
- Pull requests

### Pre-commit Testing

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest -m unit --tb=short
```

## Test Data

### Sample Data Files

Test fixtures are in `tests/fixtures/`:
- Sample CSV files
- Mock Google Sheets responses
- Configuration files

### Generating Test Data

```python
# In conftest.py
@pytest.fixture
def sample_data():
    """Create sample test data."""
    return {
        'key': 'value'
    }
```

## Troubleshooting

### Tests Fail with Import Errors

```bash
# Make sure you're in the dashboard directory
cd dashboard

# Install in development mode
pip install -e .
```

### Tests Fail with Missing Dependencies

```bash
# Reinstall requirements
pip install -r requirements.txt
```

### Tests Pass Locally but Fail in CI

- Check environment variables
- Check file paths (use Path() instead of hardcoded strings)
- Check for timezone-dependent tests

### Slow Tests

```bash
# Show slowest tests
pytest --durations=10

# Skip slow tests
pytest -m "not slow"
```

## Best Practices

1. **Write tests first** (TDD) when adding new features
2. **Keep tests fast** - unit tests should run in <100ms each
3. **Use descriptive names** - test names should explain what they test
4. **One assertion per test** (when possible) for clear failure messages
5. **Use fixtures** to avoid code duplication
6. **Mock external services** to keep tests fast and reliable
7. **Test edge cases** - empty data, None values, invalid input
8. **Keep tests independent** - tests should not depend on each other

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Python Testing with pytest (Book)](https://pragprog.com/titles/bopytest/)
