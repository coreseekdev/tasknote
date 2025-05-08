# TaskNotes

A task management tool that uses markdown for recording tasks. TaskNotes integrates with the git ecosystem, allowing you to manage tasks with commands like `git task`.

## Features

- Record tasks in markdown format
- Parse markdown using myst-parser
- Command-line interface that integrates with git
- Full Python type annotations

## Installation

TaskNotes requires Python 3.8+ and uses a conda environment.

```bash
# Activate the conda environment
conda activate tasknote

# Install the package in development mode
pip install -e .
```

## Usage

TaskNotes can be used directly or through git:

```bash
# Direct usage
tasknotes list

# Git integration
git task list
```

## Development

This project uses modern Python development tools:

- `pyproject.toml` for project configuration
- Type annotations throughout the codebase
- pytest for testing

To set up the development environment:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT
