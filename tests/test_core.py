import pytest

from repo_checkup.core import Context, GitError, Result, Status


def test_result_constructors():
    assert Result.ok("fine") == Result(Status.PASS, "fine", None)
    assert Result.warn("meh", "tip") == Result(Status.WARN, "meh", "tip")
    assert Result.fail("bad", "tip") == Result(Status.FAIL, "bad", "tip")


def test_for_path_finds_root_from_subdirectory(make_repo):
    repo = make_repo({"src/app.py": "print('hi')\n"})
    ctx = Context.for_path(repo / "src")
    assert ctx.root.samefile(repo)


def test_for_path_outside_a_repository_raises(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(GitError):
        Context.for_path(plain)


def test_git_failure_raises(make_repo):
    ctx = Context(make_repo())
    with pytest.raises(GitError):
        ctx.git("no-such-command")


def test_tracked_files_lists_committed_files_only(make_repo):
    repo = make_repo({"a.txt": "a", "sub/with space.txt": "b"})
    (repo / "untracked.txt").write_text("c", encoding="utf-8")
    assert Context(repo).tracked_files() == ["a.txt", "sub/with space.txt"]


def test_find_file_ignores_case_and_directories(make_repo):
    repo = make_repo({"ReadMe.MD": "hello", "license/notes.txt": "not a file match"})
    ctx = Context(repo)
    assert ctx.find_file("README.md").name == "ReadMe.MD"
    assert ctx.find_file("LICENSE") is None


def test_find_file_respects_name_order(make_repo):
    repo = make_repo({"README": "plain", "README.md": "markdown"})
    assert Context(repo).find_file("README.md", "README").name == "README.md"
