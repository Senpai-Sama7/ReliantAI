# Changelog

All notable changes to the ReliantAI Platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Robust setup wizard (`scripts/setup_wizard.py`) with getpass for secrets, timestamped backups, and unattended mode
- Pre-commit hooks for code quality and secret detection
- Enhanced CI pipeline with mypy type checking and yamllint YAML validation
- Comprehensive test suite for setup wizard functionality
- Contributing guidelines and development workflow documentation

### Changed
- Moved interactive setup from root `setup.py` to `scripts/setup_wizard.py`
- Normalized `.env.example` to use ASCII-only characters (removed Unicode box-drawing)
- Updated `.gitignore` to properly ignore environment configuration files

### Removed
- `.env.production` and `.env.staging` from repository tracking (converted to example templates)
- Fragile string-based environment variable replacement

### Fixed
- Security: Secrets no longer echoed to terminal during setup
- Portability: Removed non-portable `shutil.copy("/dev/null", ...)` usage
- Compatibility: Fixed encoding issues with Unicode characters in configuration files
- Setup: Environment variable detection now handles trailing comments correctly

### Security
- Added gitleaks configuration with enhanced secret pattern detection
- Removed committed environment files to prevent accidental credential exposure
- Implemented UTF-8 encoding for all file operations

## [Previous Versions]

Prior release history can be found in git tags. Use:
```bash
git log --oneline --all
git show <tag>
```

---

## Guidelines for This Changelog

When making changes, add entries to the `[Unreleased]` section under appropriate categories:

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Features soon to be removed
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related fixes

Use past tense ("Added", "Changed") for clarity.

### Release Process

When releasing a new version:

1. Update all instances of version number
2. Replace `[Unreleased]` section with new version and date:
   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD
   ```
3. Add a link at the bottom:
   ```markdown
   [Unreleased]: https://github.com/Senpai-Sama7/ReliantAI/compare/vX.Y.Z...HEAD
   [X.Y.Z]: https://github.com/Senpai-Sama7/ReliantAI/releases/tag/vX.Y.Z
   ```
4. Tag the release in git:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```
