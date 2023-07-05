import os
import re
import sys
import venv
from subprocess import CalledProcessError, CompletedProcess, check_call, run
from types import SimpleNamespace
from typing import Dict, Generator, Iterable, List, Literal, Optional, Tuple

import rtoml

from start.logger import Detail, Error, Info, Prompt, Success, Warn

# Default virtual environment directory names for searching.
DEFAULT_ENV = [".venv", ".env", "venv"]
# subprocess use gbk in PIPE decoding and can't to change, due to
# UnicodeDecodeError when some package's meta data contains invalid characters.
# Refer: https://github.com/python/cpython/issues/50385
os.environ["PYTHONIOENCODING"] = "utf-8"

BRANCH = "├─"
END = "└─"
LINE = "│ "
INDENT = "  "


def display_activate_cmd(env_dir: str):
    """Display the activate command for the virtual environment.

    Args:
        env_dir (str): Path to the virtual environment directory
    Returns:
        cmd: The command to activate the virtual environment
    """
    active_scripts = {
        "Windows": "activate",
        "bash": "activate",
        "zsh": "activate",
        "fish": "activate.fish",
        "csh": "activate.csh",
        "tcsh": "activate.csh",
        "Powershell": "Activate.ps1",
    }

    if os.name == "nt":
        bin_path = os.path.join(env_dir, "Scripts", active_scripts["Windows"])
    elif shell := os.path.basename(os.getenv("SHELL", "")):
        bin_path = os.path.join(env_dir, "bin", active_scripts[shell])
    else:
        Warn("Unknown shell, decide for yourself how to activate the virtual environment.")
        return ""

    active_cmd = os.path.join(".", os.path.relpath(bin_path, os.getcwd()))
    Prompt("Run this command to activate the virtual environment: " + active_cmd)
    return active_cmd


def neat_package_name(name: str) -> str:
    """Lower and fix unexpected characters from package name.

    '[optional]': remove
    '!', '<', '>', '=': split once and take the first part
    '_': replace with '-'

    Args:
        name: Package name
    Returns:
        Neat package name
    """
    if name.endswith("]"):
        name = re.sub(r"\[.*?\]$", "", name)

    name = re.split(r"[!<>=]", name, 1)[0]
    name = name.lower().replace("_", "-")
    return name


def try_git_init(repo_dir: str = "."):
    """Try to init a git repository in repo_dir"""
    if os.path.exists(os.path.join(repo_dir, ".git")):
        Info("Git repository already exists.")
        return
    try:
        check_call(["git", "init", repo_dir])
        os.environ["HAS_GIT"] = "1"
        Info("Git repository initialized.")
    except OSError:
        Warn("Git not found, skip git init.")
    except CalledProcessError as e:
        Error("Git init failed: ", e.output.decode("utf-8"))


class DependencyManager:
    """Package manage related functions"""

    @classmethod
    def ensure_config(cls, config: dict):
        """Ensure the config contains tool.start.dependencies and
        tool.start.dev-dependencies.

        Args:
            config: Config dict, parse from toml file
        """
        if not config.get("project"):
            config["project"] = {
                "dependencies": [],
                "optional-dependencies": {"dev": []},
            }
        if not config["project"].get("dependencies"):
            config["project"]["dependencies"] = {}
        if not config["project"].get("optional-dependencies"):
            config["project"]["optional-dependencies"] = {"dev": []}
        if not isinstance(config["project"]["dependencies"], list):
            Error("project.dependencies is not a list, start fix it.")
            config["project"]["dependencies"] = []
        if not isinstance(config["project"]["optional-dependencies"]["dev"], list):
            Error("project.optional-dependencies.dev is not a list, start fix it.")
            config["project"]["optional-dependencies"]["dev"] = []

    @classmethod
    def load_dependencies(
        cls, config_path: str, dev: bool = False, neat: bool = False
    ) -> List[str]:
        """Try to load dependency list from the config path.

        Args:
            config_path: Path to the config file
            dev: Load dev-dependencies if True, otherwise load dependencies
            neat: remove '[]' in package name that was optional installed
        """
        if config_path.endswith(".toml"):
            with open(config_path, encoding="utf8") as f:
                config = rtoml.load(f)
                cls.ensure_config(config)
                packages = config["project"]["dependencies"]
                if dev:
                    packages = config["project"]["optional-dependencies"]["dev"]
        elif config_path.endswith(".txt"):
            with open(config_path, encoding="utf8") as f:
                packages = [
                    line for _line in f if (line := _line.strip()) and line[0] not in "#-/!"
                ]
        else:
            Error("Not found dependencies due to unsupported file format: " + config_path)
            packages = []

        if neat:
            packages = [neat_package_name(p) for p in packages]

        return packages

    @classmethod
    def modify_dependencies(
        cls,
        method: Literal["add", "remove"],
        packages: Iterable[str],
        file: str,
        dev: bool = False,
    ):
        """Change the dependencies in specified file(Only support toml file).

        Args:
            method: "add" or "remove"
            packages: Packages to add or remove
            file: Config file name
            dev: Add packages as development dependency
        """
        if not (file_path := cls.ensure_path(file)):
            Error("No dependency file found")
            return

        with open(file_path, encoding="utf8") as f:
            config = rtoml.load(f)
            cls.ensure_config(config)

        dependencies: list = (
            config["project"]["dependencies"]
            if not dev
            else config["project"]["optional-dependencies"]["dev"]
        )

        if method == "add":
            for package in packages:
                if package not in dependencies:
                    dependencies.append(package)
            dependencies.sort()
        elif method == "remove":
            neat_dependencies = [neat_package_name(p) for p in dependencies]
            for package in packages:
                if package in neat_dependencies:
                    dependencies.pop(neat_dependencies.index(package))
                    neat_dependencies.remove(package)

        with open(file_path, "w", encoding="utf8") as f:
            rtoml.dump(config, f, pretty=True)

        Success("Updated dependency file: " + file_path)

    @classmethod
    def ensure_path(cls, basename: str, parent: int = 2) -> Optional[str]:
        """Find the file or folder from current path to parent directories.

        Args:
            basename: File or folder name
            parent: Parent directory depth
        Returns:
            the absolute path of the file or folder if found, otherwise None
        """
        for i in range(parent):
            path = os.path.join(os.getcwd(), *[".."] * i, basename)
            if os.path.exists(path):
                return path
        return None

    @classmethod
    def find_executable(cls) -> str:
        """Find available executable in the system. If virtual environment
        was activated, return the interpreter path which is in VIRTUAL_ENV
        bin directory, else start will find .venv, .env as env_path. If not
        find any, return sys.executable.

        Returns:
            The path of available interpreter
        """
        base_interpreter = os.path.basename(sys.executable)
        bin_dir = "Scripts" if sys.platform.startswith("win") else "bin"
        if env_path := os.getenv("VIRTUAL_ENV"):
            return os.path.join(env_path, bin_dir, base_interpreter)
        for path in DEFAULT_ENV:
            if env_path := cls.ensure_path(path):
                Info(
                    f"Found virtual environment '{env_path}' but was not "
                    "activated, packages was installed by this interpreter"
                )
                display_activate_cmd(env_path)
                return os.path.join(env_path, bin_dir, base_interpreter)
        return base_interpreter


class PipManager:
    """Parse the pip output to get the install or uninstall information.

    Args:
        executable: The python executable path
    """

    stdout: List[str]
    stderr: List[str]
    return_code: int

    def __init__(self, executable: str):
        self.cmd = [executable, "-m", "pip"]
        self.execu = executable

    def execute(self, cmd: List[str]):
        """Execute the pip command."""
        cmd = self.cmd + cmd
        try:
            self.set_outputs(run(cmd, capture_output=True, check=True))
        except CalledProcessError as output:
            self.set_outputs(output)
        self.show_output(cmd)
        return self

    def install(self, *packages: str, upgrade: bool = False) -> List[str]:
        """Install packages.

        Args:
            packages: Packages to install
            upgrade: Upgrade packages
        Returns:
            packages: Success installed packages
        """
        cmd = ["install"]
        if upgrade:
            cmd.append("-U")
        Info("Start install packages: " + ", ".join(packages))
        self.execute([*cmd, *packages])

        installed_packages = set(
            [package for line in self.stdout for package in self.parse_output(line)]
        )
        return [package for package in packages if neat_package_name(package) in installed_packages]

    def uninstall(self, *packages: str) -> List[str]:
        """Uninstall packages.

        Args:
            packages: Packages to uninstall
        Returns:
            packages: Success uninstalled packages
        """
        self.execute(["uninstall", "-y", *packages])
        return [*packages]

    def set_outputs(self, output: CompletedProcess | CalledProcessError):
        """Set the outputs that to be parse."""
        self.stdout = (
            self.decode(output.stdout).strip().replace("\r", "").split("\n")
            if output.stdout
            else []
        )
        self.stderr = (
            self.decode(output.stderr).strip().replace("\r", "").split("\n")
            if output.stderr
            else []
        )
        self.return_code = output.returncode
        return self

    def decode(self, output: bytes):
        """Decode the output to utf8 or gbk."""
        try:
            return output.decode("utf8")
        except UnicodeDecodeError:
            return output.decode("gbk")

    def show_output(self, cmd: List[str]):
        """Display the pip command output"""
        for line in self.stdout:
            line = line.strip()
            if line.startswith("Requirement already satisfied"):
                Warn(line)
            if line.startswith("Successfully"):
                Success(line)
        if self.stderr:
            Error(f"Command: {' '.join(cmd)}")
            Detail("\n".join(self.stderr))

    def parse_output(self, output: str) -> List[str]:
        """Parse the output of pip to extract the package name."""
        output = output.strip()
        if output.startswith("Requirement already satisfied"):
            return [neat_package_name(output.split()[3])]
        if output.startswith("Successfully installed"):
            return [name.rsplit("-", 1)[0] for name in output.split()[2:]]
        return []

    def parse_list_output(self) -> List[str]:
        """Parse the pip list output to get the installed packages' name."""
        return [package.lower().split()[0] for package in self.stdout[2:]]

    def analyze_packages_require(self, *packages: str) -> List[Dict]:
        """Analyze the packages require by pip show output, display as tree.

        Args:
            packages: Packages to analyze
        Returns:
            analyzed_packages: Requirement analyzed packages.
        """
        self.execute(["show", *packages])

        # format of pip show output:
        packages_require, name = {}, ""
        for line in self.stdout:
            if line.startswith("Name"):
                name = line.lstrip("Name:").strip()
                name = neat_package_name(name)
            if line.startswith("Requires") and name:
                requires = line.lstrip("Requires:").strip().split(", ")
                packages_require[name] = [neat_package_name(r) for r in requires if r]

        # parse require tree
        requires_set = set(packages_require.keys())
        for name, requires in packages_require.items():
            for i, require in enumerate(requires):
                if require in requires_set:
                    requires_set.remove(require)
                requires[i] = {require: packages_require.get(require, [])}

        return [{name: info} for name, info in packages_require.items() if name in requires_set]

    @classmethod
    def generate_dependency_tree(
        cls,
        name: str,
        dependencies: List[Dict],
        last_item: bool = False,
        prev_prefix: str = "",
    ) -> Generator[Tuple[str, str], None, None]:
        """Display dependencies as a tree

        Args:
            name: Current package name.
            dependencies: Current package's dependencies.
            last_item: Whether current package is lats item in tree.
            prev_prefix: Tree prefix of previous level's package
        Return:
            Package name and Corresponding string of package in tree.
        """
        if prev_prefix.endswith(END):
            prev_prefix = prev_prefix.replace(END, INDENT)
        if prev_prefix.endswith(BRANCH):
            prev_prefix = prev_prefix.replace(BRANCH, LINE)
        prefix = prev_prefix + (END if last_item else BRANCH)
        yield name, prefix

        for i, dependency in enumerate(dependencies):
            for name, sub_dependencies in dependency.items():
                yield from cls.generate_dependency_tree(
                    name, sub_dependencies, i == len(dependencies) - 1, prefix
                )


class ExtEnvBuilder(venv.EnvBuilder):
    """Extend environment builder to install packages.

    Args:
        packages: Packages to install after create the virtual environment
        require: Dependency file name, toml file or plain text file.
        force: Remove the existing virtual environment if it exists
        without_pip: Dont install pip in the virtual environment
        without_upgrade: Dont upgrade core package(pip & setuptools) and
            packages to install in the virtual environment
        without_system_packages: Dont give the virtual environment access
            to system packages
    """

    def __init__(
        self,
        packages: List[str] | None = None,
        require: str = "",
        force: bool = False,
        without_pip: bool = False,
        without_upgrade: bool = False,
        without_system_packages: bool = False,
    ):
        super().__init__(
            clear=force,
            system_site_packages=not without_system_packages,
            with_pip=not without_pip,
        )
        self.packages = packages or []
        if require:
            self.packages.extend(DependencyManager.load_dependencies(require))
        self.upgrade_packages = not without_upgrade

    def post_setup(self, context: SimpleNamespace):
        """Install and upgrade packages after created environment."""
        if self.with_pip and (self.upgrade_packages or self.packages):
            pip = PipManager(context.env_exe)
            if self.upgrade_packages:
                Info("Upgrading core packages...")
                pip.install("pip", "setuptools", upgrade=True)
            if self.packages:
                Info("Start installing packages...")
                pip.install(*self.packages)

        display_activate_cmd(context.env_dir)
        try_git_init(os.path.dirname(os.path.abspath(context.env_dir)))
