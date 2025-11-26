# SCP (Static Code Profiler)

AST-based static analyzer for Python code.
Measures CC/LEN/NEST and file-level quality metrics, then generates charts and an interactive HTML report.

## Usage
```bash
poetry install
poetry run cyclocalc <path> -t 5 --plots --html --json output/result.json
