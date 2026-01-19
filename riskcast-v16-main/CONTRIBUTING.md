# Contributing to RISKCAST

Thank you for your interest in contributing to RISKCAST! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- MySQL (optional, for database features)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd riskcast-v16-main
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

5. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

## Code Style

### Python

- Follow PEP 8 style guide
- Use type hints for function parameters and return types
- Maximum line length: 100 characters
- Use `black` for code formatting (optional but recommended)

```bash
black app/
```

### JavaScript/TypeScript

- Use ES6+ features
- Use meaningful variable names
- Comment complex logic
- Follow existing code style

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_sanitizer.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only fast tests (skip slow tests)
pytest -m "not slow"
```

### Writing Tests

- Write tests for new features
- Use descriptive test names
- Test edge cases
- Aim for >50% code coverage

### Test Structure

```
tests/
├── unit/          # Unit tests (fast)
├── integration/   # Integration tests (slower)
└── fixtures/      # Test data
```

## Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new features
   - Update documentation if needed

3. **Run tests**
   ```bash
   pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: description of changes"
   ```

   Use conventional commit messages:
   - `Add:` for new features
   - `Fix:` for bug fixes
   - `Update:` for updates
   - `Refactor:` for refactoring
   - `Docs:` for documentation

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub

## Code Review Guidelines

- Be respectful and constructive
- Focus on code quality and correctness
- Ask questions if something is unclear
- Suggest improvements, not just problems

## Reporting Bugs

When reporting bugs, please include:

1. **Description** - Clear description of the bug
2. **Steps to reproduce** - Step-by-step instructions
3. **Expected behavior** - What should happen
4. **Actual behavior** - What actually happens
5. **Environment** - Python version, OS, etc.
6. **Screenshots** - If applicable

## Feature Requests

When requesting features:

1. **Describe the feature** - Clear description
2. **Explain the use case** - Why is this needed?
3. **Suggest implementation** - If you have ideas
4. **Consider alternatives** - Are there existing solutions?

## Questions?

If you have questions:

- Open an issue for discussion
- Check existing documentation
- Review existing code for examples

---

Thank you for contributing! 🚀

