# Contributing to ISBN Normalization Pipeline

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/isbn-normalization-pipeline.git
cd isbn-normalization-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e .[dev]
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-normalizer`
- `bugfix/fix-isbn10-validation`
- `docs/update-readme`

### Commit Messages

Follow conventional commit format:
```
type(scope): brief description

Longer description if needed

Fixes #issue-number
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements

Example:
```
feat(normalizer): add support for Bengali numerals

Added conversion mapping for Bengali digits (০-৯) to ASCII.
This extends support for multilingual ISBN processing.

Fixes #42
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_isbn_pipeline.py

# Run specific test
pytest tests/test_isbn_pipeline.py::TestISBNNormalizer::test_validate_isbn10_valid
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Use descriptive test names
- Include docstrings explaining what is being tested

Example:
```python
def test_normalize_isbn_with_arabic_numerals():
    """Test normalization of ISBN containing Arabic-Indic numerals."""
    normalizer = ISBNNormalizer()
    raw = "٩٧٨٦٠٠١٠٠٢٥٤٠"
    expected = "9786001002540"
    result = normalizer.normalize_isbn(raw)
    assert result == expected
```

## Submitting Changes

### Pull Request Process

1. **Update your fork**
   ```bash
   git remote add upstream https://github.com/original/isbn-normalization-pipeline.git
   git fetch upstream
   git merge upstream/main
   ```

2. **Create pull request**
   - Provide a clear description of changes
   - Reference related issues
   - Include test results
   - Update documentation if needed

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement

   ## Related Issues
   Fixes #issue-number

   ## Testing
   - [ ] All existing tests pass
   - [ ] New tests added
   - [ ] Tested with sample data

   ## Checklist
   - [ ] Code follows project style
   - [ ] Documentation updated
   - [ ] Tests added/updated
   - [ ] No breaking changes
   ```

## Coding Standards

### Python Style Guide

Follow PEP 8 with these specifics:

- **Line length**: Maximum 100 characters
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings, single for dict keys
- **Imports**: Group by standard library, third-party, local

### Documentation

- **Docstrings**: Use Google style docstrings
  ```python
  def normalize_isbn(self, raw_text: str) -> Optional[str]:
      """
      Normalize ISBN from raw text.
      
      Args:
          raw_text: Raw text potentially containing ISBN
          
      Returns:
          Normalized ISBN string or None if invalid
          
      Example:
          >>> normalizer = ISBNNormalizer()
          >>> normalizer.normalize_isbn("ISBN: 978-0-19-515307-1")
          '9780195153071'
      """
  ```

- **Comments**: Use for complex logic, not obvious code
- **Type hints**: Use for all function parameters and returns

### Code Organization

- **One class per file** when possible
- **Group related functions** together
- **Keep functions short** (< 50 lines preferred)
- **Use meaningful names** for variables and functions

### Error Handling

```python
# Good
try:
    isbn = normalize_isbn(raw_text)
except ValueError as e:
    logger.error(f"Invalid ISBN format: {e}")
    return None

# Avoid bare exceptions
try:
    isbn = normalize_isbn(raw_text)
except:  # ❌ Don't do this
    pass
```

## Adding New Features

### New Numeral System Support

To add support for a new numeral system:

1. Add mapping in `ISBNNormalizer.NUMERAL_MAPPINGS`
2. Update `convert_numerals()` method
3. Add test cases
4. Update documentation

Example:
```python
BENGALI_TO_ASCII = {
    '০': '0', '১': '1', '২': '2', # ... complete mapping
}
```

### New OCR Error Patterns

To add new OCR confusion patterns:

1. Update `CONFUSION_DICT` in `ISBNNormalizer`
2. Add test cases with examples
3. Document the pattern in comments

## Documentation Updates

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features
- Keep CHANGELOG.md current

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Reach out to maintainers

## Recognition

Contributors will be acknowledged in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing! 🎉
