import json
import subprocess
import sys

import pytest

from repo_checkup import __version__
from repo_checkup.cli import EXIT_ERROR, EXIT_FAILED, EXIT_OK, main

GOOD_README = (
    "# demo\n\nA small tool that checks repositories for common engineering conventions.\n"
)


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"repo-checkup {__version__}"


def test_list_shows_checks(capsys):
    assert main(["--list"]) == EXIT_OK
    assert "readme" in capsys.readouterr().out


def test_healthy_repo_passes(make_repo, capsys):
    repo = make_repo({"README.md": GOOD_README})
    assert main([str(repo)]) == EXIT_OK
    out = capsys.readouterr().out
    assert "[PASS] readme" in out
    assert "Score: 100/100" in out


def test_failing_check_sets_exit_code(make_repo, capsys):
    repo = make_repo()
    assert main([str(repo)]) == EXIT_FAILED
    out = capsys.readouterr().out
    assert "[FAIL] readme" in out
    assert "       -> " in out


def test_defaults_to_current_directory(make_repo, monkeypatch, capsys):
    monkeypatch.chdir(make_repo({"README.md": GOOD_README}))
    assert main([]) == EXIT_OK


def test_json_format(make_repo, capsys):
    repo = make_repo()
    assert main([str(repo), "--format", "json"]) == EXIT_FAILED
    data = json.loads(capsys.readouterr().out)
    assert data["score"] == 0
    assert data["checks"][0]["id"] == "readme"
    assert data["checks"][0]["status"] == "fail"


def test_directory_outside_a_repository_is_an_error(tmp_path, capsys):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert main([str(plain)]) == EXIT_ERROR
    assert "error" in capsys.readouterr().err


def test_missing_path_is_an_error(tmp_path, capsys):
    assert main([str(tmp_path / "nope")]) == EXIT_ERROR
    assert "not a directory" in capsys.readouterr().err


def test_module_entry_point_end_to_end(make_repo):
    repo = make_repo({"README.md": GOOD_README})
    proc = subprocess.run(
        [sys.executable, "-m", "repo_checkup", str(repo), "--format", "json"],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == EXIT_OK, proc.stderr
    assert json.loads(proc.stdout)["score"] == 100
