"""Run checks, score the results and render them as text or JSON."""

import json
from dataclasses import dataclass
from pathlib import Path

from repo_checkup import __version__
from repo_checkup.core import Check, Context, Result, Status

# A pass is worth one point and a warning half a point; counted in halves to stay exact.
HALF_POINTS = {Status.PASS: 2, Status.WARN: 1, Status.FAIL: 0}


@dataclass(frozen=True)
class Entry:
    check: Check
    result: Result


@dataclass(frozen=True)
class Report:
    root: Path
    entries: list[Entry]

    @property
    def summary(self) -> dict[str, int]:
        return {s.value: sum(e.result.status is s for e in self.entries) for s in Status}

    @property
    def score(self) -> int:
        """0-100, rounded half up; 100 when there is nothing to check."""
        n = len(self.entries)
        if n == 0:
            return 100
        half_points = sum(HALF_POINTS[e.result.status] for e in self.entries)
        return (100 * half_points + n) // (2 * n)

    @property
    def failed(self) -> bool:
        return any(e.result.status is Status.FAIL for e in self.entries)


def run_checks(ctx: Context, checks: list[Check]) -> Report:
    entries = []
    for check in checks:
        try:
            result = check.run(ctx)
        except Exception as exc:  # one broken check must not hide the others
            result = Result.fail(
                f"internal error: {exc!r}", "This is a bug in repo-checkup, please report it"
            )
        entries.append(Entry(check, result))
    return Report(ctx.root, entries)


def render_text(report: Report) -> str:
    width = max((len(e.check.id) for e in report.entries), default=0)
    lines = [f"repo-checkup {__version__}  {report.root.as_posix()}", ""]
    for e in report.entries:
        lines.append(f"[{e.result.status.upper()}] {e.check.id:<{width}}  {e.result.message}")
        if e.result.suggestion:
            lines.append(f"       -> {e.result.suggestion}")
    s = report.summary
    lines += [
        "",
        f"Score: {report.score}/100  (pass {s['pass']}, warn {s['warn']}, fail {s['fail']})",
    ]
    return "\n".join(lines)


def to_dict(report: Report) -> dict:
    return {
        "tool": "repo-checkup",
        "version": __version__,
        "path": report.root.as_posix(),
        "score": report.score,
        "summary": report.summary,
        "checks": [
            {
                "id": e.check.id,
                "title": e.check.title,
                "status": e.result.status.value,
                "message": e.result.message,
                "suggestion": e.result.suggestion,
            }
            for e in report.entries
        ],
    }


def render_json(report: Report) -> str:
    return json.dumps(to_dict(report), indent=2)
