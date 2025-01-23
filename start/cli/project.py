from os import path

from typer import Context, Exit

from start.cli import params as _p
from start.core.dependency import DependencyManager
from start.core.env_builder import ExtEnvBuilder
from start.core.pip_manager import PipManager
from start.core.template import Template
from start.logger import Error, Info, Success
from start.utils import ensure_path


def new(
    ctx: Context,
    project_name: _p.ProjectName,
    packages: _p.Packages = None,
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

    Info(f"Start {'creating' if project_name != '.' else 'initializing'} project: {project_name}")
    # Create project directory from template
    Template(project_name=project_name, template_name=template).create()
    # Create virtual environment
    ExtEnvBuilder(
        packages=packages,
        require=require,
        force=force,
        verbose=verbose,
        with_pip=with_pip,
        upgrade_core=not without_upgrade,
        system_site_packages=not without_system_packages,
        pip_args=ctx.args,
    ).create(path.join(project_name, vname))
    Success("Finish creating virtual environment.")
    # modify dependencies in pyproject.toml
    DependencyManager(path.join(project_name, "pyproject.toml")).add(packages or [], save=True)
    Success("Finish creating project.")


def init(
    ctx: Context,
    packages: _p.Packages = None,
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
        ctx=ctx,
        project_name=".",
        packages=packages,
        require=require,
        vname=vname,
        force=force,
        verbose=verbose,
        template=template,
        with_pip=with_pip,
        without_upgrade=without_upgrade,
        without_system_packages=without_system_packages,
    )


def install(ctx: Context, require: _p.Require = "", verbose: _p.Verbose = False):
    """Install packages in specified dependency file."""

    if require:
        packages = DependencyManager(require).packages()
    elif file := (ensure_path("pyproject.toml") or ensure_path("requirements.txt")):
        packages = DependencyManager(file).packages()
    else:
        Error("No dependency file found")
        raise Exit(1)
    packages = [str(dep) for dep in packages]
    PipManager(verbose=verbose).install(*packages, pip_args=ctx.args)
