import ast
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import typer

from cyclocalc.analyzer.metrics import (
    collect_func_metrics,
    collect_file_metrics,
)

from cyclocalc.report.visualizer import (
    plot_cc_distribution,
    plot_len_distribution,
    plot_file_heatmap,
)

from cyclocalc.report.report_generator import (
    generate_html_report,
    build_summary,     # ✅ 为 JSON 导出复用
    detect_smells,     # ✅ 为 JSON 导出复用
)

app = typer.Typer(
    help="Analyze cyclomatic complexity and quality indicators of Python functions/methods."
)


def get_python_files(path: str, ignore: Optional[List[str]] = None) -> List[str]:
    """
    Given a path to a file or directory, return a list of all Python files.
    ignore: list of substrings. Any file path containing one of them will be skipped.
    """
    ignore = ignore or []
    p = Path(path)

    def _skip(fp: Path) -> bool:
        s = str(fp)
        return any(ig in s for ig in ignore)

    if p.is_file():
        if p.suffix == ".py":
            if _skip(p):
                return []
            return [str(p)]
        else:
            raise FileNotFoundError(f"File '{path}' is not a Python file.")

    if p.is_dir():
        python_files = [
            str(f) for f in p.rglob("*.py")
            if not _skip(f)
        ]
        if python_files:
            return python_files
        else:
            raise FileNotFoundError(
                f"No Python files found in directory '{path}' (after ignore filter)."
            )

    raise FileNotFoundError(f"Path '{path}' is not a file or directory.")


def parse_source_to_ast(file_path: str) -> Tuple[ast.AST, str]:
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source, filename=file_path), source


def list_functions(tree: ast.AST) -> List[Tuple[str, ast.AST]]:
    functions: list[tuple[str, ast.AST]] = []
    scope_stack: List[str] = []

    class FunctionVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef):
            scope_stack.append(node.name)
            self.generic_visit(node)
            scope_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef):
            scope_stack.append(node.name)
            full_name = ".".join(scope_stack)
            functions.append((full_name, node))
            self.generic_visit(node)
            scope_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            scope_stack.append(node.name)
            full_name = ".".join(scope_stack)
            functions.append((full_name, node))
            self.generic_visit(node)
            scope_stack.pop()

    FunctionVisitor().visit(tree)
    return functions


def collect_python_files(paths: List[str], ignore: Optional[List[str]] = None) -> List[str]:
    ignore = ignore or []
    all_files = []
    for path in paths:
        try:
            files = get_python_files(path, ignore=ignore)
            all_files.extend(files)
        except Exception as e:
            typer.secho(f"Error accessing {path}: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    if not all_files:
        typer.secho(
            "No Python files found after applying ignore filters.",
            fg=typer.colors.YELLOW,
            err=True,
        )
        raise typer.Exit(code=1)

    return all_files


def generate_results(
    all_files: List[str],
    threshold: int
) -> Tuple[List[str], List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
    func_results: List[str] = []
    file_summaries: List[str] = []
    func_stats: List[Dict[str, Any]] = []
    file_stats: List[Dict[str, Any]] = []

    for file_path in all_files:
        try:
            tree, source = parse_source_to_ast(file_path)
            fm = collect_file_metrics(tree, source)

            file_stats.append({
                "file": file_path,
                "comment_ratio": fm.comment_ratio,
                "docstring_coverage": fm.docstring_coverage,
                "long_line_ratio": fm.long_line_ratio,
                "naming_issue_ratio": fm.naming_issue_ratio,
                "unused_imports_count": len(fm.unused_imports),
                "unused_imports": fm.unused_imports,
            })

            file_summaries.append(
                f"{file_path}: "
                f"COMMENT_RATIO={fm.comment_ratio:.2f}, "
                f"DOCSTRING_COV={fm.docstring_coverage:.2f}, "
                f"LONG_LINE_RATIO={fm.long_line_ratio:.2f}, "
                f"NAMING_ISSUE_RATIO={fm.naming_issue_ratio:.2f}, "
                f"UNUSED_IMPORTS={len(fm.unused_imports)}"
            )

            functions = list_functions(tree)
            for func_name, func_node in functions:
                m = collect_func_metrics(func_node)

                func_stats.append({
                    "file": file_path,
                    "name": func_name,
                    "cc": m.cc,
                    "length": m.length if m.length is not None else 0,
                    "nest": m.max_nest if m.max_nest is not None else 0,
                    "lineno": getattr(func_node, "lineno", None)
                })

                if m.cc >= threshold:
                    func_results.append(
                        f"{file_path}: Function '{func_name}' "
                        f"CC={m.cc}, LEN={m.length}, NEST={m.max_nest}"
                    )

        except (SyntaxError, UnicodeDecodeError) as e:
            typer.secho(
                f"Skipping {file_path} due to parse error: {e}",
                fg=typer.colors.YELLOW,
                err=True,
            )
        except Exception as e:
            typer.secho(
                f"Error processing {file_path}: {e}",
                fg=typer.colors.RED,
                err=True
            )

    return func_results, file_summaries, func_stats, file_stats


def output_results(
    func_results: List[str],
    file_summaries: List[str],
    output: Optional[str],
) -> None:
    lines: List[str] = []
    lines.append("=== Function-level Results (filtered by CC threshold) ===")
    if func_results:
        lines.extend(func_results)
    else:
        lines.append("(No functions exceeded threshold)")
    lines.append("")
    lines.append("=== File-level Quality Summaries ===")
    if file_summaries:
        lines.extend(file_summaries)
    else:
        lines.append("(No files analyzed)")

    if output:
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            typer.secho(f"Results saved to {output}", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(
                f"Failed to write to {output}: {e}",
                fg=typer.colors.RED,
                err=True
            )
            raise typer.Exit(code=1)
    else:
        for line in lines:
            typer.echo(line)


@app.command()
def analyze(
    paths: List[str] = typer.Argument(..., help="Python files or directories"),
    threshold: int = typer.Option(1, "-t", "--threshold", help="CC threshold"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Save text output"),
    plots: bool = typer.Option(False, "--plots", help="Generate charts"),
    charts_dir: str = typer.Option("output/charts", "--charts-dir", help="Charts folder"),
    html: bool = typer.Option(False, "--html", help="Generate HTML report"),
    html_path: str = typer.Option("output/report.html", "--html-path", help="HTML path"),
    top: int = typer.Option(10, "--top", help="Top N risky functions"),

    # ✅ 新增：ignore 过滤
    ignore: List[str] = typer.Option(
        [],
        "--ignore",
        help="Ignore files/dirs containing these substrings. Can be repeated."
    ),

    # ✅ 新增：JSON 导出
    json_path: Optional[str] = typer.Option(
        None,
        "--json",
        help="Export structured results to JSON file"
    ),
):
    all_files = collect_python_files(paths, ignore=ignore)
    func_results, file_summaries, func_stats, file_stats = generate_results(all_files, threshold)
    output_results(func_results, file_summaries, output)

    out_dir = Path(charts_dir)
    if plots or html:
        out_dir.mkdir(parents=True, exist_ok=True)
        plot_cc_distribution(func_stats, out_dir)
        plot_len_distribution(func_stats, out_dir)
        plot_file_heatmap(func_stats, file_stats, out_dir)

    if plots:
        typer.secho(f"\nCharts saved to: {out_dir.resolve()}", fg=typer.colors.GREEN)

    if html:
        report_path = Path(html_path)
        generate_html_report(
            func_stats=func_stats,
            file_stats=file_stats,
            charts_dir=out_dir,
            out_path=report_path,
            top_n=top,
        )
        typer.secho(f"HTML report saved to: {report_path.resolve()}", fg=typer.colors.GREEN)

    # ✅ JSON 导出（复用报告里的 summary/smells）
    if json_path:
        jp = Path(json_path)
        summary = build_summary(func_stats, file_stats)
        smells = detect_smells(func_stats, file_stats)
        payload = {
            "summary": summary,
            "functions": func_stats,
            "files": file_stats,
            "smells": smells,
            "config": {
                "threshold": threshold,
                "ignore": ignore,
            }
        }
        jp.parent.mkdir(parents=True, exist_ok=True)
        jp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        typer.secho(f"JSON exported to: {jp.resolve()}", fg=typer.colors.GREEN)
