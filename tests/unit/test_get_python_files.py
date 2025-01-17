import pytest

from cyclocalc.cli import get_python_files  # replace with your actual module name


def test_single_python_file(tmp_path):
    # Single Python file at root level
    py_file = tmp_path / "test_file.py"
    py_file.write_text("print('hello')")
    result = get_python_files(str(py_file))
    assert result == [str(py_file)]


def test_directory_with_nested_python_files(tmp_path):
    # Create Python files at root and nested directories
    py_file_root = tmp_path / "root_file.py"
    py_file_root.write_text("print('root')")

    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    py_file_nested = nested_dir / "nested_file.py"
    py_file_nested.write_text("print('nested')")

    deeper_nested_dir = nested_dir / "deeper"
    deeper_nested_dir.mkdir()
    py_file_deeper = deeper_nested_dir / "deeper_file.py"
    py_file_deeper.write_text("print('deeper')")

    result = get_python_files(str(tmp_path))
    expected_files = {str(py_file_root), str(py_file_nested), str(py_file_deeper)}
    assert set(result) == expected_files


def test_no_python_files_in_nested_structure_raises(tmp_path):
    # Create nested directories with no Python files
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    (nested_dir / "file.txt").write_text("not python")

    deeper_nested_dir = nested_dir / "deeper"
    deeper_nested_dir.mkdir()
    (deeper_nested_dir / "file.md").write_text("still not python")

    with pytest.raises(FileNotFoundError, match="No Python files found"):
        get_python_files(str(tmp_path))
