# CycloCalc

CycloCalc is a command-line tool that analyzes Python source code by parsing its Abstract Syntax Tree (AST) to measure
cyclomatic complexity. It generates security-related metrics to help identify code areas prone to vulnerabilities.

## Features

- Analyze cyclomatic complexity of Python functions and methods
- Support for analyzing individual files or entire directories recursively
- Reports functions exceeding a configurable complexity threshold
- Outputs results to console or saves to a file
- Built with Typer for an intuitive CLI experience

## Installation

It is recommended to install CycloCalc using [pipx](https://pipx.pypa.io/) to maintain an isolated environment:

```bash
pipx install https://github.com/pewiok/cyclocalc/archive/master.zip
```

## Usage

Run the `cyclocalc analyze` command with one or more Python files or directories as arguments:

```bash
cyclocalc analyze path/to/file_or_dir [additional_paths ...] [--threshold <int>] [--output <file>]
```

- `paths`: One or more Python source files or directories to analyze
- `--threshold` (`-t`): Minimum cyclomatic complexity to report (default: 1)
- `--output` (`-o`): Optional file path to save the results instead of printing to console

Example:

```bash
cyclocalc analyze my_project/ -t 5 -o complexity_report.txt
```

This command analyzes all Python files in `my_project/`, reporting functions with complexity 5 or higher, saving the
output to `complexity_report.txt`.

## Development

The project uses Poetry for dependency management and packaging. To set up a development environment:

```bash
poetry install
```

Run tests with:

```bash
poetry run pytest
```

## Credits

- Project scaffolded using [Cookiecutter Typer](https://github.com/chamoda/cookiecutter-typer)
- Solution for missing `poetry-plugin-export` found
  [here](https://github.com/litebird/litebird_sim/issues/367#issuecomment-2724960233)

## License

This project is licensed under the GPL-2.0-only license.
