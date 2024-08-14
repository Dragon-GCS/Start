from os import path

from typer import Argument, Option

from start.core.dependency import DependencyManager
from start.core.env_builder import ExtEnvBuilder
from start.core.pip_manager import PipManager
from start.logger import Error, Info, Success
from start.core.template import Template


def new(
    project_name: str = Argument(
        help="Name of the project", show_default=False, autocompletion=None
    ),
    packages: list[str] = Option(
        None,
        "-p",
        "--packages",
        help="Packages to install after create the virtual environment",
        show_default=False,
    ),
    require: str = Option(
        "", "-r", "--require", help="Dependency file name. Toml file or plain text file"
    ),
    vname: str = Option(".venv", "-n", "--vname", help="Name of the virtual environment"),
    force: bool = Option(
        False, "-f", "--force", help="Remove the existing virtual environment if it exists"
    ),
    verbose: bool = Option(False, "-v", "--verbose", help="Display install details"),
    template: str = Option("", help="Use a template from local or a git repository"),
    with_pip: bool = Option(
        True, "--with-pip/--without-pip", help="Install pip in the virtual environment"
    ),
    without_upgrade: bool = Option(
        False,
        "--without-upgrade",
        help="Don't upgrade core package(pip & setuptools) and all packages to be installed in the virtual environment",
    ),
    without_system_packages: bool = Option(
        False,
        "--without-system-packages",
        help="Don't give the virtual environment access to system packages",
    ),
):
    """Create a new project and virtual environment, install the specified packages."""

    Info(
        f"Start {'creating' if project_name != '.' else 'initializing'} " f"project: {project_name}"
    )
    ExtEnvBuilder(
        packages=packages,
        require=require,
        force=force,
        verbose=verbose,
        with_pip=with_pip,
        without_upgrade=without_upgrade,
        without_system_packages=without_system_packages,
    ).create(path.join(project_name, vname))
    Success("Finish creating virtual environment.")
    # Create project directory from template
    Template(project_name=project_name, vname=vname).create(template)
    # modify dependencies in pyproject.toml
    DependencyManager.modify_dependencies(
        "add", packages or [], path.join(project_name, "pyproject.toml")
    )
    Success("Finish creating project.")


def init(
    packages: list[str] = Option(
        None,
        "-p",
        "--packages",
        help="Packages to install after create the virtual environment",
        show_default=False,
    ),
    require: str = Option(
        "", "-r", "--require", help="Dependency file name. Toml file or plain text file"
    ),
    vname: str = Option(".venv", "-n", "--vname", help="Name of the virtual environment"),
    force: bool = Option(
        False, "-f", "--force", help="Remove the existing virtual environment if it exists"
    ),
    verbose: bool = Option(False, "-v", "--verbose", help="Display install details"),
    template: str = Option("", help="Use a template from local or a git repository"),
    with_pip: bool = Option(
        True, "--with-pip/--without-pip", help="Install pip in the virtual environment"
    ),
    without_upgrade: bool = Option(
        False,
        "--without-upgrade",
        help="Don't upgrade core package(pip & setuptools) and all packages to be installed in the virtual environment",
    ),
    without_system_packages: bool = Option(
        False,
        "--without-system-packages",
        help="Don't give the virtual environment access to system packages",
    ),
):
    """Use current directory as the project name and create a new project at the current directory."""

    return new(
        ".",
        packages,
        require=require,
        vname=vname,
        force=force,
        verbose=verbose,
        template=template,
        with_pip=with_pip,
        without_upgrade=without_upgrade,
        without_system_packages=without_system_packages,
    )


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
