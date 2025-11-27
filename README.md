[English](README.md) | [中文](README_zh.md)


# SCP (Static Code Profiler)

**SCP** is an AST-based static analysis tool for Python projects.  
It profiles code complexity and quality risks using **multiple metrics**, visualizes results, and generates an **interactive HTML report**.

> SCP = **Static Code Profiler**  
> A lightweight yet practical multi-metric risk analyzer for Python source code.

---

## ✨ Highlights

- **Pure static analysis** via Python `ast` (no execution required)
- **Multi-metric profiling**
  - Function-level: **CC / LEN / NEST**
  - File-level: **comment ratio / docstring coverage / long-line ratio / naming issues / unused imports**
- **Risk grading + Smells** (Low / Medium / High)
- **Visual analytics**
  - CC distribution plot  
  - LEN distribution plot  
  - **File-level risk heatmap**
- **Interactive HTML report**
  - Top risky files & functions  
  - Smells list  
  - Embedded plots  
  - **Expandable source preview** for top risky functions
- **Engineering-ready CLI**
  - Threshold filter, ignore paths, JSON export, plots & report output
- **Windows executables**
  - Command-line `cyclocalc.exe`
  - Optional GUI launcher for non-CLI users

---

## 📌 What SCP Measures

### Function-level Metrics

| Metric | Meaning | How we compute (AST-based) |
|---|---|---|
| **CC** (Cyclomatic Complexity) | Branch/path complexity; higher means more error-prone | Count decision nodes (`if/for/while/try/except/with/...`) + boolean ops |
| **LEN** (Length) | Function size (LOC), longer usually harder to maintain | `end_lineno - lineno + 1` |
| **NEST** (Max Nesting Depth) | Structural depth of control blocks | DFS over nested `If/For/While/Try/With/...` |

### File-level Metrics

| Metric | Meaning |
|---|---|
| **COMMENT_RATIO** | Proportion of comment lines |
| **DOCSTRING_COV** | Coverage across module/class/function docstrings |
| **LONG_LINE_RATIO** | Ratio of lines longer than 79 chars (PEP8) |
| **NAMING_ISSUE_RATIO** | Naming violations vs. snake_case / CapWords |
| **UNUSED_IMPORTS** | Imported names never referenced (semantic risk) |

---

## 🧠 Risk Levels & Smells

SCP maps multi-metrics to **risk levels** and generates "smells":

- **High risk**
  - `CC ≥ 10`  
  - `LEN ≥ 60`
  - `NEST ≥ 5`

- **Medium risk**
  - `CC ≥ 7`
  - `LEN ≥ 40`
  - `NEST ≥ 3`
  - Low docstring / low comments / high long-line / naming issues / unused imports

- **Low risk**
  - Everything else

These smells are shown in CLI output and HTML report for quick diagnosis.

---

## 🚀 Quick Start

### 1) Install dependencies (Poetry)

```bash
poetry install
```

### 2) Run analysis

```bash
poetry run cyclocalc <path_to_project_or_file> -t 5 --plots --html
```

Example:

```bash
poetry run cyclocalc cyclocalc/ -t 5 --plots --html --json output/result.json
```

---

## 🖥️ CLI Options

```bash
cyclocalc [PATHS...] [OPTIONS]
```

| Option | Description |
|---|---|
| `-t, --threshold` | Minimum CC to show in function list |
| `--plots` | Generate charts (CC/LEN distribution + heatmap) |
| `--charts-dir` | Directory to save charts *(default: output/charts)* |
| `--html` | Generate interactive HTML report |
| `--html-path` | Path for HTML report *(default: output/report.html)* |
| `--json` | Export structured JSON results |
| `--ignore` | Ignore paths containing substring (repeatable) |
| `--top` | Top N risky functions shown in HTML |
| `-o, --output` | Save plain-text CLI output to a file |

---

## 📊 Outputs

After running with `--plots --html --json`, SCP generates:

```
output/
 ├─ charts/
 │   ├─ cc_distribution.png
 │   ├─ len_distribution.png
 │   └─ file_heatmap.png
 ├─ report.html
 └─ result.json
```

### Report Screenshots

- **CC Distribution**

  ![cc](output/charts/cc_distribution.png)

- **LEN Distribution**

  ![len](output/charts/len_distribution.png)

- **File-level Risk Heatmap**

  ![heatmap](output/charts/file_heatmap.png)

---

## 🖥️ Windows Executables

If you are on Windows and prefer not to install a Python environment, download the executables from the **GitHub Releases** page.

Release package contains:

```
CycloCalc_release/
  cyclocalc.exe        # CLI executable
  CycloCalc_GUI.exe    # Optional GUI launcher
```

### Using `cyclocalc.exe` (CLI)

```bat
cyclocalc.exe <PATHS...> -t 10 --plots --html --json report.json
```

### Using `CycloCalc_GUI.exe` (GUI)

Double-click `CycloCalc_GUI.exe`, choose target paths and options, then click **Run**.
Make sure `CycloCalc_GUI.exe` and `cyclocalc.exe` stay in the **same folder**.

---

## 🧩 Project Structure

```
cyclocalc/
 ├─ analyzer/
 │   └─ metrics.py            # all metric extraction (AST-based)
 ├─ report/
 │   ├─ visualizer.py         # plots + heatmap (matplotlib)
 │   └─ report_generator.py   # HTML rendering + smells + source preview
 ├─ cli.py                    # Typer CLI entry
 └─ __init__.py
run_cli.py                    # wrapper entry for packaging/CLI execution
packaging/                    # optional: GUI + packaging helpers
```

---

## 🔍 Why Python (and why SCP)

This project demonstrates Python’s strengths in **static analysis + tooling**:

- `ast` for compiler-front-end style parsing  
- `dataclasses` and rich data structures for metric modeling  
- `typer` for modern CLI engineering  
- `matplotlib` for scientific visualization  
- built-in `json/html/pathlib` for practical report generation

SCP forms a complete workflow:

**analyze → evaluate → visualize → report → locate risk**

---

## 🛠️ Development

Run locally:

```bash
poetry run cyclocalc cyclocalc/ -t 5
```

Run tests:

```bash
poetry run pytest
```

### Packaging (for developers)

Build CLI exe:

```bat
poetry run pyinstaller -F -n cyclocalc --hidden-import typer run_cli.py
```

Build GUI exe:

```bat
poetry run pyinstaller -F -w -n CycloCalc_GUI packaging/gui_cyclocalc.py
```

---

## 🧭 Roadmap (Optional)

- More semantic smells (e.g., broad except, mutable defaults)
- Trend comparison (`--compare old.json new.json`)
- Interactive sorting/filtering in HTML tables

---

## 🙏 Credits

- Base project scaffold from **CycloCalc** (Typer CLI + CC analyzer)
- Extended into SCP with multi-metric profiling, visualization, and reports

---

## 📄 License

GPL-2.0-only
