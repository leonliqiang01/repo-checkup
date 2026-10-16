"""Find checks by importing every module in a package."""

import importlib
import inspect
import pkgutil
from types import ModuleType

from repo_checkup import checks as builtin_checks
from repo_checkup.core import Check


def discover(package: ModuleType = builtin_checks) -> list[Check]:
    """Instantiate every ``Check`` subclass defined in ``package``'s modules.

    Modules whose name starts with ``_`` are skipped. Checks are sorted by
    ``(order, id)``; a duplicate id raises ``ValueError``.
    """
    found: dict[str, Check] = {}
    for info in pkgutil.iter_modules(package.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{package.__name__}.{info.name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            # Skip the base class and checks merely imported from elsewhere.
            if not issubclass(cls, Check) or cls is Check or cls.__module__ != module.__name__:
                continue
            if cls.id in found:
                raise ValueError(f"duplicate check id {cls.id!r} in {module.__name__}")
            found[cls.id] = cls()
    return sorted(found.values(), key=lambda check: (check.order, check.id))
