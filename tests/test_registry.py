import importlib
import pkgutil
import re
import sys
from pathlib import Path

import pytest

from repo_checkup import checks
from repo_checkup.registry import discover

TESTS_DIR = Path(__file__).parent
KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

CHECK_SOURCE = """
from repo_checkup.core import Check, Result

class {name}(Check):
    id = "{id}"
    title = "{id} title"
    order = {order}

    def run(self, ctx):
        return Result.ok("fine")
"""


# --- Conventions every built-in check must follow -------------------------------------


def test_builtin_checks_have_unique_kebab_case_ids_and_titles():
    found = discover()
    ids = [check.id for check in found]
    assert len(ids) == len(set(ids))
    for check in found:
        assert KEBAB_CASE.match(check.id), check.id
        assert check.title.strip(), check.id


def test_every_check_module_has_its_own_test_file():
    modules = [m.name for m in pkgutil.iter_modules(checks.__path__) if not m.name.startswith("_")]
    missing = [m for m in modules if not (TESTS_DIR / "checks" / f"test_{m}.py").is_file()]
    assert not missing, f"add tests/checks/test_<name>.py for: {missing}"


# --- Discovery mechanics, exercised on a throwaway package ----------------------------


@pytest.fixture
def fake_package(tmp_path, monkeypatch):
    """Build an importable package from ``{module_name: source}`` and import it."""
    created = []

    def make(modules: dict[str, str]):
        name = f"fake_checks_{len(created)}"
        pkg = tmp_path / name
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        for module, source in modules.items():
            (pkg / f"{module}.py").write_text(source, encoding="utf-8")
        monkeypatch.syspath_prepend(str(tmp_path))
        created.append(name)
        return importlib.import_module(name)

    yield make
    for key in list(sys.modules):
        if key.split(".")[0] in created:
            del sys.modules[key]


def check_source(name: str, id: str, order: int) -> str:
    return CHECK_SOURCE.format(name=name, id=id, order=order)


def test_discover_finds_checks_in_every_module_sorted_by_order_then_id(fake_package):
    pkg = fake_package(
        {
            "alpha": check_source("Alpha", "alpha", 20),
            "beta": check_source("Beta", "beta", 10),
            "gamma": check_source("Gamma", "gamma", 10),
        }
    )
    assert [check.id for check in discover(pkg)] == ["beta", "gamma", "alpha"]


def test_discover_ignores_imported_checks_and_private_modules(fake_package):
    pkg = fake_package(
        {
            "_helpers": check_source("Hidden", "hidden", 10),
            "alpha": check_source("Alpha", "alpha", 10),
            "beta": "from .alpha import Alpha\n" + check_source("Beta", "beta", 20),
        }
    )
    assert [check.id for check in discover(pkg)] == ["alpha", "beta"]


def test_discover_rejects_duplicate_ids(fake_package):
    pkg = fake_package(
        {"one": check_source("One", "same", 10), "two": check_source("Two", "same", 20)}
    )
    with pytest.raises(ValueError, match="duplicate check id 'same'"):
        discover(pkg)
