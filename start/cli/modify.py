from typing import Literal

from typer import Exit

from start.cli import params as _p
from start.core.dependency import DependencyManager
from start.core.pip_manager import PipManager
from start.logger import Warn


def _modify(
    *packages: str,
    method: Literal["add", "remove"],
    dev: bool = False,
    dependency: str = "pyproject.toml",
    verbose: bool = False,
):
    if not dependency.endswith(".toml"):
        Warn("Only support toml file now")
        raise Exit(1)
    pip = PipManager(DependencyManager.find_executable(), verbose=verbose)
    operate = pip.install if method == "add" else pip.uninstall
    result = operate(*packages)
    if result:
        DependencyManager.modify_dependencies(
            method=method, packages=result, file=dependency, dev=dev
        )


def add(
    packages: _p.Packages,
    dev: _p.Dev = False,
    dependency: _p.Dependency = "pyproject.toml",
    verbose: _p.Verbose = False,
):
    """Install packages and add to the dependency file."""

    _modify(*packages, method="add", dev=dev, dependency=dependency, verbose=verbose)


def remove(
    packages: _p.Packages,
    dev: _p.Dev = False,
    dependency: _p.Dependency = "pyproject.toml",
    verbose: _p.Verbose = False,
):
    """Uninstall packages and remove from the dependency file."""

    _modify(*packages, method="remove", dev=dev, dependency=dependency, verbose=verbose)
