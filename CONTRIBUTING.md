# Contributing to ZeroCAC

Thank you for your interest in contributing to ZeroCAC. We welcome contributions from developers, growth marketers, and AI enthusiasts.

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### 1. Reporting Bugs
* Check existing issues before opening a new one.
* Use the provided Bug Report issue template.
* Include clear steps to reproduce, expected vs actual behavior, and environment details.

### 2. Suggesting Features
* Open an issue using the Feature Request template.
* Describe the use case and why it benefits organic product distribution.

### 3. Pull Requests
* Always branch from `main`: `git checkout -b feat/your-feature-name`.
* Follow Conventional Commits: `feat(scope): description` or `fix(scope): description`.
* Do not commit secrets, API keys, or large binary files.
* Ensure all tests pass: `pytest`.
* Write clean, typed Python code adhering to PEP 8 standards.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/PatelDeepB/zerocac.git
cd zerocac

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies in editable mode with dev tools
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env

# Run tests
pytest
```

## Pull Request Checklist
* [ ] Code adheres to project coding guidelines.
* [ ] Unit tests added or updated.
* [ ] Documentation updated if applicable.
* [ ] All tests passing locally.
