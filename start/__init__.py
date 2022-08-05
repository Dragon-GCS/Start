import os
import sys
from typing import List

import fire
import rtoml

from start.template import Template

from .manager import DependencyManager, ExtEnvBuilder, PipManager
from .color import Cyan, Red, Yellow


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
        print(Cyan("Args:"))
        print(Yellow(f"project_name: {project_name}"))
        print(Yellow(f"vname: {vname}"))
        print(Yellow(f"packages: {packages}"))
        print(Yellow(f"flags: {force or ''} {without_pip or ''}"
                     f"{without_upgrade or ''} {without_system_packages or ''}"))
        env_path = os.path.join(project_name, vname)
        ExtEnvBuilder(
            packages=packages,
            force=force,
            without_pip=without_pip,
            without_upgrade=without_upgrade,
            without_system_packages=without_system_packages
        ).create(env_path)
        # Create project directory from template
        Template(project_name=project_name).create()
        # modify dependencies in pyproject.toml
        DependencyManager.modify_dependencies(
            "add", packages, os.path.join(project_name, "pyproject.toml"))

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
        dependency: str = "pyproject.toml"
    ):
        """Install packages in specified dependency file.

        Args:
            dependency:
                Dependency file name. If given a toml file, start will parse
                "tool.start.dependencies", else start will parse each line as
                a package name to install. As default, if not found
                "pyproject.toml", start will try to find "requirements.txt"
                When virtual environment is not activated, start will try to
                find interpreter in .venv, .env orderly.
        """
        if file := DependencyManager.ensure_path("pyproject.toml"):
            with open(file, encoding="utf-8") as f:
                packages: List[str] = rtoml.load(f)["project"]["dependencies"]
        elif file := DependencyManager.ensure_path("requirements.txt"):
            with open(file, encoding="utf-8") as f:
                packages = f.read().splitlines()
        else:
            print(Red("No dependency file found"))
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
        PipManager(DependencyManager.find_executable()).install(packages)
        DependencyManager.modify_dependencies("add", packages, dependency)
        print(Cyan("Updated dependency file"))

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
        PipManager(DependencyManager.find_executable()).uninstall(packages)
        DependencyManager.modify_dependencies("remove", packages, dependency)
        print(Cyan("Updated dependency file"))


def main():
    fire.Fire(Start)
