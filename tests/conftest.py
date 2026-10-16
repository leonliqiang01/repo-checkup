import itertools
import subprocess
from pathlib import Path

import pytest


def _run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8", check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout


@pytest.fixture(autouse=True)
def isolated_git(tmp_path_factory, monkeypatch):
    """Keep the developer's own git setup (autocrlf, excludes, signing...) out of tests."""
    home = tmp_path_factory.mktemp("githome")
    empty = home / "empty"
    empty.write_text("", encoding="utf-8")
    config = home / "config"
    config.write_text(
        "[user]\n\tname = Test User\n\temail = test@example.com\n"
        "[init]\n\tdefaultBranch = main\n"
        "[commit]\n\tgpgsign = false\n"
        f"[core]\n\tautocrlf = false\n\texcludesFile = {empty.as_posix()}\n"
        f"\tattributesFile = {empty.as_posix()}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    # Stop git from finding a repository above the test directories.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path_factory.getbasetemp()))


@pytest.fixture
def git():
    """Run git inside a test repository: ``git(repo, "log", "--oneline")``."""
    return _run_git


@pytest.fixture
def make_repo(tmp_path):
    """Create a real git repository under ``tmp_path`` and return its path.

    ``files`` maps relative paths to text or bytes. Unless ``commit`` is None,
    everything is committed with that message (an empty commit if there are no files).
    """
    counter = itertools.count()

    def make(
        files: dict[str, str | bytes] | None = None,
        commit: str | None = "chore: initial commit",
    ) -> Path:
        repo = tmp_path / f"repo{next(counter)}"
        repo.mkdir()
        _run_git(repo, "init", "-q")
        for rel, content in (files or {}).items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
        if commit is not None:
            _run_git(repo, "add", "-A")
            _run_git(repo, "commit", "-q", "--allow-empty", "-m", commit)
        return repo

    return make
