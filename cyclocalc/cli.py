import ast
from pathlib import Path
from typing import List, Tuple

import typer

app = typer.Typer(
    help="Analyze cyclomatic complexity of Python functions/methods in files or directories."
)


def get_python_files(path: str) -> List[str]:
    """
    Given a path to a file or directory, return a list of all Python files.

    Args:
        path (str): File or directory path.

    Returns:
        List[str]: List of Python file paths.

    Raises:
        FileNotFoundError: If the path is neither a file nor a directory,
            or if no Python files are found in the directory.
    """
    p = Path(path)

    if p.is_file():
        if p.suffix == ".py":
            return [str(p)]
        else:
            raise FileNotFoundError(f"File '{path}' is not a Python file.")

    if p.is_dir():
        python_files = [str(f) for f in p.rglob("*.py")]
        if python_files:
            return python_files
        else:
            raise FileNotFoundError(f"No Python files found in directory '{path}'.")

    raise FileNotFoundError(f"Path '{path}' is not a file or directory.")


def parse_source_to_ast(file_path: str) -> ast.AST:
    """
    Parse Python source file into an AST.

    Args:
        file_path (str): Path to Python source file.

    Returns:
        ast.AST: Parsed AST tree.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source, filename=file_path)


def list_functions(tree: ast.AST) -> List[Tuple[str, ast.AST]]:
    """
    List all function and method definitions in the AST with their full names,
    including parent classes and enclosing functions.

    Args:
        tree (ast.AST): AST tree of a Python source file.

    Returns:
        List[Tuple[str, ast.AST]]: List of tuples (full_function_name, function_node).
    """
    functions: list[tuple[str, ast.AST]] = []
    scope_stack: List[str] = []

    class FunctionVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef):
            # Push class name onto scope stack
            scope_stack.append(node.name)
            self.generic_visit(node)
            scope_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef):
            # Push function name onto scope stack
            scope_stack.append(node.name)
            full_name = ".".join(scope_stack)
            functions.append((full_name, node))
            self.generic_visit(node)
            scope_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            # Push async function name onto scope stack
            scope_stack.append(node.name)
            full_name = ".".join(scope_stack)
            functions.append((full_name, node))
            self.generic_visit(node)
            scope_stack.pop()

    FunctionVisitor().visit(tree)
    return functions


def calculate_cyclomatic_complexity(func_node: ast.AST) -> int:
    """
    Calculate cyclomatic complexity of a single function/method AST node.

    Complexity = 1 + number of decision points:
    Decision points include: if, for, while, and, or, except, with, assert, elif, try, finally

    Args:
        func_node (ast.AST): AST node of a function or method.

    Returns:
        int: Cyclomatic complexity.
    """
    complexity = 1  # Base complexity

    # Nodes that increase complexity by 1 each occurrence
    decision_nodes = (
        ast.If,
        ast.For,
        ast.While,
        ast.ExceptHandler,
        ast.With,
        ast.Assert,
        ast.Try,
        ast.AsyncFor,
        ast.AsyncWith,
    )

    # Boolean operators 'and' and 'or' increase complexity per occurrence
    bool_ops = (ast.And, ast.Or)

    # Walk all nodes inside the function
    for node in ast.walk(func_node):
        if isinstance(node, decision_nodes):
            complexity += 1
        elif isinstance(node, ast.BoolOp) and isinstance(node.op, bool_ops):
            # Each boolean operator counts as complexity for each value except the first
            complexity += len(node.values) - 1

    return complexity


@app.command()
def analyze(
    path: str = typer.Argument(..., help="Python source file or directory to analyze"),
    threshold: int = typer.Option(
        1, "-t", "--threshold", help="Minimum cyclomatic complexity to report"
    ),
    output: str = typer.Option(
        None, "-o", "--output", help="File path to save the results instead of printing"
    ),
):
    """
    Analyze cyclomatic complexity of Python functions/methods in files or directories.
    """
    try:
        files = get_python_files(path)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    results = []

    for file_path in files:
        try:
            tree = parse_source_to_ast(file_path)
            functions = list_functions(tree)
            for func_name, func_node in functions:
                complexity = calculate_cyclomatic_complexity(func_node)
                if complexity >= threshold:
                    results.append(
                        f"{file_path}: Function '{func_name}' has cyclomatic complexity {complexity}"
                    )
        except (SyntaxError, UnicodeDecodeError) as e:
            typer.secho(
                f"Skipping {file_path} due to parse error: {e}",
                fg=typer.colors.YELLOW,
                err=True,
            )
        except Exception as e:
            typer.secho(
                f"Error processing {file_path}: {e}", fg=typer.colors.RED, err=True
            )

    if output:
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write("\n".join(results))
            typer.secho(f"Results saved to {output}", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(
                f"Failed to write to {output}: {e}", fg=typer.colors.RED, err=True
            )
            raise typer.Exit(code=1)
    else:
        for line in results:
            typer.echo(line)
