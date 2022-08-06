import os
from typing import List

import fire
import rtoml

from start.template import Template

from .manager import DependencyManager, ExtEnvBuilder, PipManager
from .logger import Info, Error, Success


class Start:
    """Package manager based on pip and venv """

    def new(
        self,
        project_name,
        *packages,
        vname: str = ".venv",
        force: bool = False,
        without_pip: bool = False,
        without_upgrade: bool = False,
        without_system_packages: bool = False
    ):
        """Create a new project. Create a virtual environment and install
        specified packages.

        Args:
            project_name:
                Name of the project
            vname:
                Name of the virtual environment, default is ".venv"
            force:
                Remove the existing virtual environment if it exists
            without_pip:
                Default to install pip in the virtual environment, add
                "--without-pip" to skip this.
            without_upgrade:
                Default to upgrade core package(pip & setuptools) and
                all packages to install in the virtual environment,
                add "--without-upgrade" to skip this.
            without_system_packages:
                Default to give the virtual environment access to system
                packages, add "--without-system-packages" to skip this.
            packages:
                Packages to install after create the virtual environment
        """
        Info(f"Start {'creating' if project_name == '.' else 'initializing'}"
             f"project: {project_name}")
        env_path = os.path.join(project_name, vname)
        if os.path.exists(env_path) and not force:
            Error(f"Virtual environment {env_path} already exists,"
                   "use --force to override")
            return
        ExtEnvBuilder(
            packages=packages,
            force=force,
            without_pip=without_pip,
            without_upgrade=without_upgrade,
            without_system_packages=without_system_packages
        ).create(env_path)
        Success("Finish creating virtual environment.")
        # Create project directory from template
        Template(project_name=project_name).create()
        # modify dependencies in pyproject.toml
        DependencyManager.modify_dependencies(
            "add", packages, os.path.join(project_name, "pyproject.toml"))
        Success("Finish creating project files.")

    def init(
        self,
        *packages,
        vname: str = ".venv",
        force: bool = False,
        without_pip: bool = False,
        without_upgrade: bool = False,
        without_system_packages: bool = False
    ):
        """Use current directory as the project name and create a new project
        at the current directory.

        Args:
            vname:
                Name of the virtual environment, default is ".venv"
            force:
                Remove the existing virtual environment if it exists
            without_pip:
                Default to install pip in the virtual environment, add
                "--without-pip" to skip this.
            without_upgrade:
                Default to upgrade core package(pip & setuptools) and
                all packages to install in the virtual environment,
                add "--without-upgrade" to skip this.
            without_system_packages:
                Default to give the virtual environment access to system
                packages, add "--without-system-packages" to skip this.
            packages:
                Packages to install after create the virtual environment
        """
        self.new(
            ".",
            *packages,
            vname=vname,
            force=force,
            without_pip=without_pip,
            without_upgrade=without_upgrade,
            without_system_packages=without_system_packages)

    def install(
        self,
        dependency: str = ""
    ):
        """Install packages in specified dependency file.

        Args:
            dependency:
                Dependency file name. If given a toml file, start will parse
                "project.dependencies", else start will parse each line as
                a package name to install. As default, if not found
                "pyproject.toml", start will try to find "requirements.txt"
                When virtual environment is not activated, start will try to
                find interpreter in .venv, .env orderly.
        """
        if dependency:
            packages = DependencyManager.load_dependencies(dependency)
        elif file := (DependencyManager.ensure_path("pyproject.toml") or
                      DependencyManager.ensure_path("pyproject.toml")):
            packages = DependencyManager.load_dependencies(file)
        else:
            Error("No dependency file found")
            return
        PipManager(DependencyManager.find_executable()).install(packages)

    def add(
        self,
        *packages,
        dev: bool = False,
        dependency: str = "pyproject.toml"
    ):
        """Install packages and add to the dependency file.

        Args:
            packages:
            dev:
                Add packages as development dependency
            dependency:
                Dependency file name, default is pyproject.toml (Only support
                toml file now). If file not exists, it will be create.
        """
        if not dependency.endswith(".toml"):
            Warning("Only support toml file now")
            return
        PipManager(DependencyManager.find_executable()).install(packages)
        DependencyManager.modify_dependencies(
            method="add", packages=packages, file=dependency, dev=dev)
        Success("Updated dependency file")

    def remove(
        self,
        *packages,
        dev: bool = False,
        dependency: str = "pyproject.toml"
    ):
        """Uninstall packages and remove from the dependency file.

        Args:
            packages:
            dev:
                Remove packages from development dependency
            dependency:
                Dependency file name, default is pyproject.toml (Only support
                toml file now). If file not exists, it will be create.
        """
        if not dependency.endswith(".toml"):
            Warning("Only support toml file now")
            return
        PipManager(DependencyManager.find_executable()).uninstall(packages)
        DependencyManager.modify_dependencies(
            method="remove", packages=packages, file=dependency, dev=dev)
        Success("Updated dependency file")


def main():
    fire.Fire(Start)
