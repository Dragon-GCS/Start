from os import path, sep
from typing import Literal

from typer import Argument, Exit, Option, Typer

from start.logger import Detail, Error, Info, Success, Warn
from start.manager import DependencyManager, ExtEnvBuilder, PipManager, env_typer
from start.template import Template

app = Typer(help="Package manager based on pip and venv", rich_markup_mode="rich")
app.add_typer(env_typer, name="env", rich_help_panel="Environment")


@app.command(rich_help_panel="Project")
def new(
    project_name: str = Argument(
        help="Name of the project", show_default=False, autocompletion=None
    ),
    packages: list[str] = Argument(
        None,
        help="Packages to install after create the virtual environment",
        show_default=False,
    ),
    require: str = Option(
        "", "-r", "--require", help="Dependency file name. Toml file or plain text file"
    ),
    vname: str = Option(".venv", "-v", "--vname", help="Name of the virtual environment"),
    force: bool = Option(
        False, "-f", "--force", help="Remove the existing virtual environment if it exists"
    ),
    verbose: bool = Option(False, "-v", "--verbose", help="Display install details"),
    without_pip: bool = Option(
        False, "--without-pip/--with-pip", help="Install pip in the virtual environment"
    ),
    without_upgrade: bool = Option(
        False,
        "--without-upgrade/--with-upgrade",
        help="Upgrade core package(pip & setuptools) and all packages to be installed in the virtual environment",
    ),
    with_template: bool = Option(
        False, "--with-template/--without-template", help="Create template files"
    ),
    without_system_packages: bool = Option(
        False,
        "--without-system-packages/--with-system-packages",
        help="Give the virtual environment access to system packages",
    ),
):
    """Create a new project and virtual environment, install the specified packages."""

    Info(
        f"Start {'creating' if project_name != '.' else 'initializing'} " f"project: {project_name}"
    )
    env_path = path.join(project_name, vname)
    if path.exists(env_path) and not force:
        Error(f"Virtual environment {env_path} already exists," "use --force to override")
        return
    packages = packages or []
    ExtEnvBuilder(
        packages=packages,
        require=require,
        force=force,
        verbose=verbose,
        without_pip=without_pip,
        without_upgrade=without_upgrade,
        without_system_packages=without_system_packages,
    ).create(env_path)
    Success("Finish creating virtual environment.")
    # Create project directory from template
    Template(project_name=project_name, vname=vname).create(with_template)
    # modify dependencies in pyproject.toml
    DependencyManager.modify_dependencies(
        "add", packages, path.join(project_name, "pyproject.toml")
    )
    Success("Finish creating project.")


@app.command(rich_help_panel="Project")
def init(
    packages: list[str] = Argument(
        None,
        help="Packages to install after create the virtual environment",
        show_default=False,
    ),
    require: str = Option(
        "", "-r", "--require", help="Dependency file name. Toml file or plain text file"
    ),
    vname: str = Option(".venv", "-v", "--vname", help="Name of the virtual environment"),
    force: bool = Option(
        False, "-f", "--force", help="Remove the existing virtual environment if it exists"
    ),
    verbose: bool = Option(False, "-v", "--verbose", help="Display install details"),
    without_pip: bool = Option(
        False, "--without-pip/--with-pip", help="Install pip in the virtual environment"
    ),
    without_upgrade: bool = Option(
        False,
        "--without-upgrade/--with-upgrade",
        help="Upgrade core package(pip & setuptools) and all packages to be installed in the virtual environment",
    ),
    with_template: bool = Option(
        False, "--with-template/--without-template", help="Create template files"
    ),
    without_system_packages: bool = Option(
        False,
        "--without-system-packages/--with-system-packages",
        help="Give the virtual environment access to system packages",
    ),
):
    """Use current directory as the project name and create a new project at the current directory."""

    new(
        ".",
        packages,
        require=require,
        vname=vname,
        force=force,
        verbose=verbose,
        without_pip=without_pip,
        without_upgrade=without_upgrade,
        with_template=with_template,
        without_system_packages=without_system_packages,
    )


@app.command(rich_help_panel="Project")
def install(
    dependency: str = Argument(
        "",
        help="Dependency file name. If given a toml file, start will parse"
        "'project.dependencies', else start will parse each line as"
        "a package name to install. As default, if not found"
        "'pyproject.toml', start will try to find 'requirements.txt'"
        "When virtual environment is not activated, start will try to"
        "find interpreter in .venv, .env orderly.",
    ),
    verbose: bool = Option(False, "-v", "--verbose", help="Display install details"),
):
    """Install packages in specified dependency file."""
    if dependency:
        packages = DependencyManager.load_dependencies(dependency)
    elif file := (
        DependencyManager.ensure_path("pyproject.toml")
        or DependencyManager.ensure_path("requirements.txt")
    ):
        packages = DependencyManager.load_dependencies(file)
    else:
        Error("No dependency file found")
        return
    PipManager(DependencyManager.find_executable(), verbose=verbose).install(*packages)


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


@app.command(rich_help_panel="Modify Dependencies")
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


@app.command(rich_help_panel="Modify Dependencies")
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


@app.command(rich_help_panel="Inspect")
def show(packages: list[str] = Argument(help="Packages to show", show_default=False)):
    """Show information about installed packages."""
    pip = PipManager(DependencyManager.find_executable())
    pip.execute(["show", *packages])
    if pip.stdout:
        Detail("\n".join(pip.stdout))
    if pip.stderr:
        Error("\n".join(pip.stderr))


@app.command(name="list", rich_help_panel="Inspect")
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
