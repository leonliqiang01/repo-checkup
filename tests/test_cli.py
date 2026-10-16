import pytest

from repo_checkup import __version__
from repo_checkup.cli import main


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"repo-checkup {__version__}"
