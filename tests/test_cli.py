from tempfile import NamedTemporaryFile

from typer.testing import CliRunner

from cyclocalc.cli import app

runner = CliRunner()


def test_empty_file():
    with NamedTemporaryFile(suffix=".py") as empty_file:
        result = runner.invoke(app, [empty_file.name])
        assert result.exit_code == 0
        assert result.stdout.strip() == ""


def test_this_file():
    result = runner.invoke(app, [__file__])
    assert result.exit_code == 0
    assert result.stdout.strip().split("\n") == [
        f"{__file__}: Function 'test_empty_file' has cyclomatic complexity 4",
        f"{__file__}: Function 'test_this_file' has cyclomatic complexity 3",
    ]
