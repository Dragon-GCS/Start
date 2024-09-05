from typing import Literal

from typer import Context, Exit

from start.cli import params as _p
from start.core.dependency import DependencyManager
from start.core.pip_manager import PipManager
from start.logger import Warn


def _modify(
    *packages: str,
    method: Literal["add", "remove"],
    group: str = "",
    dependency: str = "pyproject.toml",
    verbose: bool = False,
    pip_args: list[str] = [],
):
    if not dependency.endswith(".toml"):
        Warn("Only support toml file now")
        raise Exit(1)
    pip = PipManager(DependencyManager.find_executable(), verbose=verbose)
    operate = pip.install if method == "add" else pip.uninstall
    result = operate(*packages, pip_args=pip_args)
    if result:
        DependencyManager(dependency).modify_dependencies(
            method=method, packages=result, group=group, save=True
        )


def add(
    ctx: Context,
    packages: _p.Packages,
    group: _p.Group = "",
    dependency: _p.Dependency = "pyproject.toml",
    verbose: _p.Verbose = False,
):
    """Install packages and add to the dependency file."""

    _modify(
        *packages or [],
        method="add",
        group=group,
        dependency=dependency,
        verbose=verbose,
        pip_args=ctx.args,
    )


def remove(
    ctx: Context,
    packages: _p.Packages,
    group: _p.Group = "",
    dependency: _p.Dependency = "pyproject.toml",
    verbose: _p.Verbose = False,
):
    """Uninstall packages and remove from the dependency file."""

    _modify(
        *packages or [],
        method="remove",
        group=group,
        dependency=dependency,
        verbose=verbose,
        pip_args=ctx.args,
    )
