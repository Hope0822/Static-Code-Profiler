import ast
import re
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple


# ----------------------------
# Dataclasses
# ----------------------------

@dataclass
class FuncMetrics:
    cc: int
    length: Optional[int] = None
    max_nest: Optional[int] = None


@dataclass
class FileMetrics:
    comment_ratio: float
    docstring_coverage: float
    long_line_ratio: float
    naming_issue_ratio: float
    naming_issues: List[str]
    unused_imports: List[str]  # ✅ 新增


# ----------------------------
# Function-level metrics
# ----------------------------

def calc_cc(func_node: ast.AST) -> int:
    complexity = 1
    decision_nodes = (
        ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Assert, ast.Try,
        ast.AsyncFor, ast.AsyncWith,
    )
    bool_ops = (ast.And, ast.Or)

    for node in ast.walk(func_node):
        if isinstance(node, decision_nodes):
            complexity += 1
        elif isinstance(node, ast.BoolOp) and isinstance(node.op, bool_ops):
            complexity += len(node.values) - 1

    return complexity


def calc_length(func_node: ast.AST) -> Optional[int]:
    if hasattr(func_node, "lineno") and hasattr(func_node, "end_lineno"):
        return func_node.end_lineno - func_node.lineno + 1
    return None


def calc_max_nesting(func_node: ast.AST) -> int:
    nest_nodes = (
        ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith,
    )

    def dfs(node: ast.AST, depth: int) -> int:
        max_d = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, nest_nodes):
                max_d = max(max_d, dfs(child, depth + 1))
            else:
                max_d = max(max_d, dfs(child, depth))
        return max_d

    return dfs(func_node, 0)


def collect_func_metrics(func_node: ast.AST) -> FuncMetrics:
    return FuncMetrics(
        cc=calc_cc(func_node),
        length=calc_length(func_node),
        max_nest=calc_max_nesting(func_node),
    )


# ----------------------------
# File-level metrics
# ----------------------------

def calc_comment_ratio(source: str) -> float:
    lines = source.splitlines()
    if not lines:
        return 0.0
    comment_lines = 0
    for line in lines:
        if line.strip().startswith("#"):
            comment_lines += 1
    return comment_lines / len(lines)


def calc_long_line_ratio(source: str, limit: int = 79) -> float:
    lines = source.splitlines()
    if not lines:
        return 0.0
    long_lines = sum(1 for line in lines if len(line.rstrip("\n")) > limit)
    return long_lines / len(lines)


# Naming regex
SNAKE_CASE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
CAPWORDS_RE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")


def _is_snake_case(name: str) -> bool:
    return bool(SNAKE_CASE_RE.match(name))


def _is_capwords(name: str) -> bool:
    return bool(CAPWORDS_RE.match(name))


def check_func_and_class_names(tree: ast.AST) -> Tuple[int, List[str]]:
    total_checked = 0
    issues: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            total_checked += 1
            if not _is_snake_case(node.name):
                issues.append(f"Function name not snake_case: {node.name}")
        elif isinstance(node, ast.AsyncFunctionDef):
            total_checked += 1
            if not _is_snake_case(node.name):
                issues.append(f"Async function name not snake_case: {node.name}")
        elif isinstance(node, ast.ClassDef):
            total_checked += 1
            if not _is_capwords(node.name):
                issues.append(f"Class name not CapWords: {node.name}")
    return total_checked, issues


def check_arg_names(tree: ast.AST) -> Tuple[int, List[str]]:
    total_checked = 0
    issues: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args + node.args.kwonlyargs:
                total_checked += 1
                if not _is_snake_case(arg.arg):
                    issues.append(f"Argument name not snake_case: {arg.arg}")
            if node.args.vararg:
                total_checked += 1
                if not _is_snake_case(node.args.vararg.arg):
                    issues.append(f"*args name not snake_case: {node.args.vararg.arg}")
            if node.args.kwarg:
                total_checked += 1
                if not _is_snake_case(node.args.kwarg.arg):
                    issues.append(f"**kwargs name not snake_case: {node.args.kwarg.arg}")
    return total_checked, issues


def check_var_names(tree: ast.AST) -> Tuple[int, List[str]]:
    store_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            store_names.add(node.id)

    total_checked = 0
    issues: List[str] = []
    for name in store_names:
        if name == "_" or (name.startswith("__") and name.endswith("__")):
            continue
        total_checked += 1
        if not _is_snake_case(name):
            issues.append(f"Variable name not snake_case: {name}")

    return total_checked, issues


def collect_naming_issues(tree: ast.AST) -> Tuple[float, List[str]]:
    total_checked = 0
    issues: List[str] = []
    for checker in (check_func_and_class_names, check_arg_names, check_var_names):
        checked, found = checker(tree)
        total_checked += checked
        issues.extend(found)
    ratio = (len(issues) / total_checked) if total_checked > 0 else 0.0
    return ratio, issues


def calc_docstring_coverage(tree: ast.AST) -> float:
    defs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.append(node)

    total_defs = len(defs) + 1  # module
    doc_with = 0

    if ast.get_docstring(tree):
        doc_with += 1
    for d in defs:
        if ast.get_docstring(d):
            doc_with += 1

    return doc_with / total_defs if total_defs > 0 else 0.0


# ✅ 新增：Unused imports（近似静态分析即可课设加分）
def calc_unused_imports(tree: ast.AST) -> List[str]:
    imported: Set[str] = set()
    used: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                imported.add(alias.asname or alias.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)

    # 忽略一些常见“导入即使用”的情况（可选）
    unused = sorted(x for x in imported if x not in used)
    return unused


def collect_file_metrics(tree: ast.AST, source: str) -> FileMetrics:
    comment_ratio = calc_comment_ratio(source)
    doc_cov = calc_docstring_coverage(tree)
    long_ratio = calc_long_line_ratio(source)
    naming_ratio, naming_issues = collect_naming_issues(tree)
    unused_imports = calc_unused_imports(tree)  # ✅ 新增

    return FileMetrics(
        comment_ratio=comment_ratio,
        docstring_coverage=doc_cov,
        long_line_ratio=long_ratio,
        naming_issue_ratio=naming_ratio,
        naming_issues=naming_issues,
        unused_imports=unused_imports,
    )
