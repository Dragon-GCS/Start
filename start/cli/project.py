from os import path

from typer import Argument, Option

from start.core.dependency import DependencyManager
from start.core.env_builder import ExtEnvBuilder
from start.core.pip_manager import PipManager
from start.logger import Error, Info, Success
from start.core.template import Template


def new(
    project_name: _p.ProjectName,
    packages: _p.Packages = [],
    require: _p.Require = "",
    vname: _p.VName = ".venv",
    force: _p.Force = False,
    verbose: _p.Verbose = False,
    template: _p.Template = "",
    with_pip: _p.WithPip = True,
    without_upgrade: _p.WithoutUpgrade = False,
    without_system_packages: _p.WithoutSystemPackages = False,
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
    packages: _p.Packages = [],
    require: _p.Require = "",
    vname: _p.VName = ".venv",
    force: _p.Force = False,
    verbose: _p.Verbose = False,
    template: _p.Template = "",
    with_pip: _p.WithPip = True,
    without_upgrade: _p.WithoutUpgrade = False,
    without_system_packages: _p.WithoutSystemPackages = False,
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


def install(require: _p.Require = "", verbose: _p.Verbose = False):
    """Install packages in specified dependency file."""

    if require:
        packages = DependencyManager.load_dependencies(require)
    elif file := (
        DependencyManager.ensure_path("pyproject.toml")
        or DependencyManager.ensure_path("requirements.txt")
    ):
        packages = DependencyManager.load_dependencies(file)
    else:
        Error("No dependency file found")
        return
    PipManager(DependencyManager.find_executable(), verbose=verbose).install(*packages)
