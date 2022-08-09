import fire

from os import path

from start.logger import Detail, Info, Error, Success, Warn
from start.manager import DependencyManager, ExtEnvBuilder, PipManager
from start.template import Template


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
        env_path = path.join(project_name, vname)
        if path.exists(env_path) and not force:
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
            "add", packages, path.join(project_name, "pyproject.toml"))
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
        PipManager(DependencyManager.find_executable()).install(*packages)

    def add(
        self,
        *packages,
        dev: bool = False,
        dependency: str = "pyproject.toml"
    ):
        """Install packages and add to the dependency file.

        Args:
            packages:
                Packages to install and record in the dependency file
            dev:
                Add packages as development dependency
            dependency:
                Dependency file name, default is pyproject.toml (Only support
                toml file now). If file not exists, it will be create.
        """
        if not dependency.endswith(".toml"):
            Warning("Only support toml file now")
            return
        PipManager(DependencyManager.find_executable()).install(*packages)
        DependencyManager.modify_dependencies(
            method="add", packages=packages, file=dependency, dev=dev)

    def remove(
        self,
        *packages,
        dev: bool = False,
        dependency: str = "pyproject.toml"
    ):
        """Uninstall packages and remove from the dependency file.

        Args:
            packages:
                Packages to uninstall and remove from the dependency file
            dev:
                Remove packages from development dependency
            dependency:
                Dependency file name, default is pyproject.toml (Only support
                toml file now). If file not exists, it will be create.
        """
        if not dependency.endswith(".toml"):
            Warning("Only support toml file now")
            return
        PipManager(DependencyManager.find_executable()).uninstall(*packages)
        DependencyManager.modify_dependencies(
            method="remove", packages=packages, file=dependency, dev=dev)

    def show(
        self,
        *packages
    ):
        """Same as "pip show" command.

        Args:
            packages:
                Packages to show

        """
        pip = PipManager(DependencyManager.find_executable())
        pip.execute(["show", *packages], check=False)
        if pip.stdout:
            Detail("\n".join(pip.stdout))
        if pip.stderr:
            Error("\n".join(pip.stderr))

    def list(
        self,
        *,
        tree: bool = False,
        dep: bool = False,
        dev: bool = False,
        dependency: str = "pyproject.toml"
    ):
        """Display all installed packages.

        Args:
            tree:
                Display installed packages in a tree structure
            dep:
                Display installed packages in a dependency file
            dev:
                Display installed packages in development dependency
            dependency:
                Dependency file name, default is pyproject.toml (Only support
                toml file now). Only take effect when "dep" or "dev"  is True.
        """
        pip = PipManager(DependencyManager.find_executable())

        status = ""
        if dep or dev:
            status = "(Dependencies)" if dep else "(Dev-Dependencies)"
            if not (config_path := DependencyManager.ensure_path(dependency)):
                Error(f"Dependency file {dependency} not found")
                return
            packages = DependencyManager.load_dependencies(
                config_path, dev=dev)
        else:
            packages = pip.execute(["list"]).parse_list_output()

        if not packages:
            Warn("No packages found")
            return

        if not tree:
            Info(f"Installed{status} packages:")
            Detail("\n".join("- " + package for package in packages))
            return

        analyzed_packages = pip.analyze_packages_require(*packages)
        Success("Analysis for installed packages:")

        Info(pip.execu if path.basename(pip.execu) == pip.execu
             else path.basename(path.abspath(pip.execu + "/../../.."))
             + status
             )

        installed_packages = set(packages)
        for i, package in enumerate(analyzed_packages):
            name, dependencies = list(package.items())[0]
            for branch, tree_string in \
                pip.generate_dependency_tree(
                    name, dependencies, i == len(analyzed_packages) - 1):
                Status = Detail if branch in installed_packages else Warn
                Detail(tree_string + Status(branch, display=False))


def main():
    fire.Fire(Start)
