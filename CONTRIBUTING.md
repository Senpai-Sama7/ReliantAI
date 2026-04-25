# Contributing to ReliantAI

Thank you for your interest in contributing to ReliantAI! This document outlines the process and guidelines for contributing code, documentation, and other improvements.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Setup for Development

1. Clone the repository:
   ```bash
   git clone https://github.com/Senpai-Sama7/ReliantAI.git
   cd ReliantAI
   ```

2. Initialize the environment:
   ```bash
   python3 scripts/setup_wizard.py
   ```
   Or for non-interactive setup:
   ```bash
   python3 scripts/setup_wizard.py -y
   ```

3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. Start services:
   ```bash
   docker compose up -d
   ```

5. Run tests:
   ```bash
   python3 -m pytest tests/ -v
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b fix/issue-description     # for bug fixes
git checkout -b feat/feature-name         # for new features
git checkout -b docs/update-description   # for documentation
```

Branch naming convention:
- `fix/` - Bug fixes
- `feat/` - New features
- `docs/` - Documentation updates
- `test/` - Test additions
- `chore/` - Refactoring, cleanup, tooling

### 2. Make Changes

- Keep commits atomic and well-scoped
- Write clear commit messages:
  ```
  type: brief description
  
  Longer explanation if needed.
  
  - Detail 1
  - Detail 2
  ```

- Follow coding standards (enforced by pre-commit):
  - Black for Python formatting
  - isort for import organization
  - flake8 for linting
  - Type hints where practical

### 3. Test Your Changes

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_setup_wizard.py -v

# Run with coverage
python3 -m pytest tests/ --cov=scripts --cov=integration
```

### 4. Validate Environment Configuration

The CI pipeline validates:
- Python code quality (black, isort, flake8)
- Type hints (mypy)
- YAML syntax (yamllint)
- Secrets (gitleaks)
- Tests (pytest)

You can run these locally:
```bash
black scripts/
isort scripts/
flake8 scripts/
mypy scripts/setup_wizard.py --ignore-missing-imports
yamllint docker-compose*.yml
pytest tests/ -v
```

### 5. Push and Create a Pull Request

```bash
git push -u origin your-branch-name
```

Then create a PR on GitHub with:
- Clear title and description
- Reference to related issues (fixes #123)
- Checklist of what's been tested

## Coding Standards

### Python

- **Style**: Black (line length 100)
- **Imports**: isort with Black profile
- **Linting**: flake8 (max complexity 10)
- **Type hints**: Use for new code, especially in `scripts/`
- **Error handling**: Be explicit about exceptions caught

Example:
```python
import os
import sys
from pathlib import Path

def process_file(path: str) -> dict:
    """Process a file and return metadata."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"size": len(content), "path": path}
    except FileNotFoundError as e:
        print(f"File not found: {path}", file=sys.stderr)
        raise
```

### Secrets and Security

- **Never commit secrets** - use placeholders (REPLACE_ME)
- **Never commit .env files** - use .env.example templates
- **Use getpass for input** of passwords/tokens
- **Environment-specific files** go to .env.*.example (e.g., .env.production.example)

### Documentation

- Use Markdown for documentation
- Include examples and usage information
- Update README when adding major features
- Add docstrings to public functions

## CI/CD Pipeline

The CI pipeline automatically runs on every pull request:

1. **Code Quality** - linting, formatting, type checking
2. **Secrets Detection** - gitleaks for leaked credentials
3. **Tests** - unit tests with pytest
4. **Docker Build** - build and push container images (if configured)
5. **Integration Tests** - smoke tests against live services
6. **Staging Deployment** - automatic (for main branch)
7. **Production Deployment** - manual trigger (for main branch)

All checks must pass before merging.

## Merge Requirements

- [ ] All CI checks pass
- [ ] At least 2 approvals from maintainers
- [ ] No merge conflicts
- [ ] Appropriate labels applied
- [ ] Related issues referenced

## Release Process

Releases are tagged with semantic versioning (vX.Y.Z):
- **Major (X)**: Breaking changes
- **Minor (Y)**: New features
- **Patch (Z)**: Bug fixes

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for design decisions
- Check existing issues and PRs before creating duplicates

Thank you for contributing!
