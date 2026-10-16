import pytest

from repo_checkup.checks.readme import Readme
from repo_checkup.core import Context, Status

REAL_CONTENT = (
    "# demo\n\n"
    "A small tool that checks repositories for common engineering conventions.\n\n"
    "## Usage\n\n"
    "    demo [path]\n"
)


def run(repo):
    return Readme().run(Context(repo))


def test_missing_readme_fails(make_repo):
    result = run(make_repo({"main.py": "print('hi')\n"}))
    assert result.status is Status.FAIL
    assert result.suggestion


@pytest.mark.parametrize("content", ["", "  \n\n\t\n"])
def test_empty_readme_fails(make_repo, content):
    result = run(make_repo({"README.md": content}))
    assert result.status is Status.FAIL
    assert "empty" in result.message


def test_headings_only_readme_is_a_stub(make_repo):
    result = run(make_repo({"README.md": "# demo\n\n## Usage\n\n## License\n"}))
    assert result.status is Status.WARN
    assert "stub" in result.message


def test_short_readme_is_a_stub(make_repo):
    result = run(make_repo({"README.md": "# demo\n\nTODO\n"}))
    assert result.status is Status.WARN


def test_rst_title_underline_counts_as_heading(make_repo):
    result = run(make_repo({"README.rst": "demo\n====\n"}))
    assert result.status is Status.WARN


def test_readme_with_real_content_passes(make_repo):
    result = run(make_repo({"README.md": REAL_CONTENT}))
    assert result.status is Status.PASS
    assert result.suggestion is None
    assert "README.md" in result.message


@pytest.mark.parametrize("name", ["readme.md", "README.rst", "README.txt", "README"])
def test_other_readme_names_are_accepted(make_repo, name):
    result = run(make_repo({name: REAL_CONTENT}))
    assert result.status is Status.PASS


def test_chinese_readme_passes(make_repo):
    content = (
        "# 演示\n\n"
        "这是一个用来检查仓库是否符合常见工程规范的命令行小工具，"
        "支持文本和 JSON 两种输出格式，可以放进 CI 使用。\n"
    )
    result = run(make_repo({"README.md": content}))
    assert result.status is Status.PASS
