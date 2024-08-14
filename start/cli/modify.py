from typing import Literal

from typer import Argument, Exit, Option

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
    packages: list[str] = Argument(
        help="Packages to install and record in the dependency file", show_default=False
    ),
    dev: bool = Option(False, "-D", "--dev", help="Add packages as development dependency"),
    dependency: str = Option(
        "pyproject.toml",
        "-d",
        "--dependency",
        help="Dependency file name, default is pyproject.toml (Only support toml file now). "
        "If file not exists, it will be created.",
    ),
    verbose: bool = Option(False, "-v", "--verbose", help="Display install details"),
):
    """Install packages and add to the dependency file."""

    _modify(*packages, method="add", dev=dev, dependency=dependency, verbose=verbose)


def remove(
    packages: list[str] = Argument(
        help="Packages to uninstall and remove from the dependency file", show_default=False
    ),
    dev: bool = Option(False, "-D", "--dev", help="Remove packages from development dependency"),
    dependency: str = Option(
        "pyproject.toml",
        "-d",
        "--dependency",
        help="Dependency file name, default is pyproject.toml (Only support toml file now). "
        "If file not exists, it will be created.",
    ),
    verbose: bool = Option(False, "-v", "--verbose", help="Display uninstall details"),
):
    """Uninstall packages and remove from the dependency file."""

    _modify(*packages, method="remove", dev=dev, dependency=dependency, verbose=verbose)
