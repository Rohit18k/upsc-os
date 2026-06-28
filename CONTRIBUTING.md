# Contributing to UPSC OS

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Run tests
6. Submit a pull request

## Development Setup

```bash
# Install pre-commit hooks
pre-commit install

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Frontend setup
cd frontend
npm install
```

## Code Standards

- Python: Black + Ruff formatting
- TypeScript/React: ESLint + Prettier
- All code must pass linting and type checking
- Tests required for all new code
- No TODO comments in committed code
- No hardcoded credentials or secrets

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure CI passes
4. Get at least one review approval
5. Squash commits before merge

## Commit Messages

Follow conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `chore:` maintenance
- `docs:` documentation
- `test:` testing
- `refactor:` refactoring
- `security:` security fix

## Security

Report security issues to security@upscos.io. Do not open public issues.
