# Joshua Libraries Test Suite

This directory contains the `pytest` test suite for the `joshua_network` and `joshua_logger` libraries.

## Prerequisites

- Python 3.10+
- The `joshua_network` and `joshua_logger` libraries must be installed or available in the `PYTHONPATH`.

## Installation

Install the required testing dependencies from the `lib/` directory:

```bash
pip install -r tests/requirements-test.txt
```

## Running Tests

To run the complete test suite, navigate to the `lib/` directory (the parent of `tests/`) and execute `pytest`:

```bash
# From the /mnt/projects/Joshua/lib/ directory
pytest tests/
```

### Running with Coverage

To generate a test coverage report, use the `pytest-cov` plugin. The following command will run tests and report on the coverage for both libraries, highlighting any lines that are not covered. The target is to maintain 80%+ coverage.

```bash
pytest --cov=joshua_network --cov=joshua_logger --cov-report term-missing tests/
```
