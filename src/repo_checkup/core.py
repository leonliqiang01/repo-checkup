"""Plugin interface shared by all checks."""

import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import ClassVar, Self


class Status(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class Result:
    status: Status
    message: str
    suggestion: str | None = None

    @classmethod
    def ok(cls, message: str) -> Self:
        return cls(Status.PASS, message)

    @classmethod
    def warn(cls, message: str, suggestion: str) -> Self:
        return cls(Status.WARN, message, suggestion)

    @classmethod
    def fail(cls, message: str, suggestion: str) -> Self:
        return cls(Status.FAIL, message, suggestion)


class GitError(RuntimeError):
    """A git command failed, or git is not installed."""


class Context:
    """What a check gets to look at: the repository root plus a few helpers."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._tracked_files: list[str] | None = None

    @classmethod
    def for_path(cls, path: Path) -> Self:
        """Build a context for the repository that contains ``path``."""
        top = cls(path).git("rev-parse", "--show-toplevel").strip()
        return cls(Path(top))

    def git(self, *args: str) -> str:
        """Run ``git -C <root> <args>`` and return its stdout."""
        try:
            proc = subprocess.run(
                ["git", "-C", str(self.root), *args],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitError("git executable not found") from exc
        if proc.returncode != 0:
            raise GitError(proc.stderr.strip() or f"git {' '.join(args)} failed")
        return proc.stdout

    def tracked_files(self) -> list[str]:
        """Paths of all tracked files, relative to the root, using ``/`` as separator."""
        if self._tracked_files is None:
            out = self.git("ls-files", "-z")
            self._tracked_files = [p for p in out.split("\0") if p]
        return self._tracked_files

    def find_file(self, *names: str) -> Path | None:
        """Return the first file in the root matching one of ``names``, ignoring case."""
        files = {p.name.lower(): p for p in self.root.iterdir() if p.is_file()}
        for name in names:
            if (match := files.get(name.lower())) is not None:
                return match
        return None


class Check:
    """Base class for checks.

    Subclass it in a module under ``repo_checkup.checks`` and the registry picks it up.
    """

    id: ClassVar[str]
    title: ClassVar[str]
    order: ClassVar[int] = 100

    def run(self, ctx: Context) -> Result:
        raise NotImplementedError
