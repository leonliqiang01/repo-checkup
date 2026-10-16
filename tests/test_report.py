import json
from pathlib import Path

import pytest

from repo_checkup.core import Check, Context, Result, Status
from repo_checkup.report import Entry, Report, render_json, render_text, run_checks


class Dummy(Check):
    id = "dummy"
    title = "Dummy"


class Boom(Check):
    id = "boom"
    title = "Boom"

    def run(self, ctx):
        raise RuntimeError("kaputt")


class Fine(Check):
    id = "fine"
    title = "Fine"

    def run(self, ctx):
        return Result.ok("all good")


def report_of(*statuses: Status, root: Path = Path(".")) -> Report:
    results = {
        Status.PASS: Result.ok("ok"),
        Status.WARN: Result.warn("meh", "do better"),
        Status.FAIL: Result.fail("bad", "fix it"),
    }
    return Report(root, [Entry(Dummy(), results[s]) for s in statuses])


P, W, F = Status.PASS, Status.WARN, Status.FAIL


@pytest.mark.parametrize(
    ("statuses", "score"),
    [
        ((), 100),
        ((P,), 100),
        ((W,), 50),
        ((F,), 0),
        ((P, P, P, W), 88),  # 87.5 rounds half up
        ((P, P, P) + (W,) * 4 + (F, F), 56),
    ],
)
def test_score(statuses, score):
    assert report_of(*statuses).score == score


def test_summary_and_failed():
    report = report_of(P, W, W, F)
    assert report.summary == {"pass": 1, "warn": 2, "fail": 1}
    assert report.failed
    assert not report_of(P, W).failed


def test_crashing_check_becomes_a_failure_without_hiding_others(tmp_path):
    report = run_checks(Context(tmp_path), [Boom(), Fine()])
    boom, fine = report.entries
    assert boom.result.status is Status.FAIL
    assert "kaputt" in boom.result.message
    assert fine.result == Result.ok("all good")


def test_render_text(tmp_path):
    text = render_text(report_of(P, F, root=tmp_path))
    lines = text.splitlines()
    assert lines[0].startswith("repo-checkup ")
    assert "[PASS] dummy  ok" in lines
    assert "[FAIL] dummy  bad" in lines
    assert "       -> fix it" in lines
    assert lines[-1] == "Score: 50/100  (pass 1, warn 0, fail 1)"


def test_render_json(tmp_path):
    data = json.loads(render_json(report_of(P, W, root=tmp_path)))
    assert data["tool"] == "repo-checkup"
    assert data["score"] == 75
    assert data["summary"] == {"pass": 1, "warn": 1, "fail": 0}
    assert data["checks"][0] == {
        "id": "dummy",
        "title": "Dummy",
        "status": "pass",
        "message": "ok",
        "suggestion": None,
    }
    assert data["checks"][1]["suggestion"] == "do better"
