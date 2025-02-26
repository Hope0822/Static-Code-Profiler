# CycloCalc

A program that analyzes source code ASTs to measure cyclomatic complexity and generate security metrics highlighting
areas susceptible to vulnerabilities.

## Installation

This project can be installed directly from the GitHub repository. Using [pipx](https://pipx.pypa.io/) is recommended to
ensure a clean, isolated installation environment and to simplify package management.

```bash
pipx install https://github.com/pewiok/cyclocalc/archive/master.zip
```

## Credits

- This project is based on a [Cookiecutter Typer](https://github.com/chamoda/cookiecutter-typer) template.
- The solution to `The requested command export does not exist.` error (missing `poetry-plugin-export`) was found
  [here](https://github.com/litebird/litebird_sim/issues/367#issuecomment-2724960233).
