from os import sep

from typer import Argument, Exit, Option

from start.core.dependency import DependencyManager
from start.core.pip_manager import PipManager
from start.logger import Detail, Error, Info, Success, Warn


def show(packages: list[str] = Argument(help="Packages to show", show_default=False)):
    """Show information about installed packages."""
    pip = PipManager(DependencyManager.find_executable())
    pip.execute(["show", *packages])
    if pip.stdout:
        Detail("\n".join(pip.stdout))
    if pip.stderr:
        Error("\n".join(pip.stderr))


def list_packages(
    tree: bool = Option(
        False, "-t", "--tree", help="Display installed packages in a tree structure"
    ),
    dev: bool = Option(
        False, "-D", "--dev", help="Display installed packages in development dependency"
    ),
    dependency: str = Option("", "-d", "--dependency", help="Dependency file name"),
):
    """Display all installed packages."""

    pip = PipManager(DependencyManager.find_executable())

    status = ""
    if dependency or dev:
        if not (config_path := DependencyManager.ensure_path(dependency)):
            Error(f"Dependency file {dependency} not found")
            raise Exit(1)
        status = "(Dependencies)" if dependency else "(Dev-Dependencies)"
        packages = DependencyManager.load_dependencies(config_path, dev=dev, neat=tree)
    else:
        packages = pip.execute(["list"]).parse_list_output()

    if not packages:
        Warn("No packages found")
        raise Exit()

    if not tree:
        Info(f"Installed{status} packages:")
        Detail("\n".join("- " + package for package in packages))
        raise Exit()

    analyzed_packages = pip.analyze_packages_require(*packages)
    Success("Analysis for installed packages:")

    Info(pip.execu.split(sep)[-4] + status if sep in pip.execu else pip.execu)

    installed_packages = set(packages)
    for i, package in enumerate(analyzed_packages):
        name, dependencies = list(package.items())[0]
        for branch, tree_string in pip.generate_dependency_tree(
            name, dependencies, i == len(analyzed_packages) - 1
        ):
            Status = Detail if branch in installed_packages else Warn
            Detail(tree_string + Status(branch, display=False))
