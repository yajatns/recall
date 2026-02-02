# Contributing to recall

Thanks for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/yajatns/recall/issues) first
2. Open a new issue with:
   - Clear title describing the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version)

### Suggesting Features

Open an issue with the `enhancement` label describing:
- What problem it solves
- Proposed solution
- Any alternatives you've considered

### Submitting Code

1. **Fork** the repo
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/recall.git
   cd recall
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Install dev dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
5. **Make your changes**
6. **Run checks**:
   ```bash
   ruff check src/
   black src/
   pytest
   ```
7. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add cool new feature"
   ```
8. **Push** and open a PR:
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code change that neither fixes a bug nor adds a feature
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Code Style

- **Formatter:** Black (line length 100)
- **Linter:** Ruff
- **Type hints:** Encouraged but not required

## Development Setup

```bash
# Clone and install
git clone https://github.com/yajatns/recall.git
cd recall
pip install -e ".[dev]"

# Run the CLI
recall --help

# Run tests
pytest

# Format code
black src/

# Lint
ruff check src/
```

## Questions?

Open an issue or start a discussion. We're happy to help!
