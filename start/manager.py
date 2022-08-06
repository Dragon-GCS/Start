import os
import subprocess
import sys
import venv

from typing import List, Literal, Optional, Sequence, Tuple
from types import SimpleNamespace

import rtoml

from .logger import Detail, Info, Success, Prompt, Error, Warn


def display_activate_cmd(env_dir: str):
    """Display the activate command for the virtual environment.

    Args:
        env_dir: Path to the virtual environment directory
    """
    active_scripts = {
        "Windows": {
            "cmd.exe": "activate.bat",
            "Powershell": "Activate.ps1"
        },
        "POSIX": {
            "bash/zsh": "activate",
            "fish": "activate.fish",
            "csh/tcsh": "activate.csh",
            "Powershell": "Activate.ps1"
        }
    }

    platform = "Windows" if sys.platform.startswith("win") else "POSIX"
    bin_path = os.path.join(env_dir, "Scripts" if platform == "Windows" else "bin")
    scripts = active_scripts[platform]
    Prompt("Select the following command to activate the virtual"
           "environment according to your shell:")
    commands = "\n".join(
        f"{shell:10}: {os.path.abspath(os.path.join(bin_path, script))}"
        for shell, script in scripts.items())
    Detail(commands)


class DependencyManager:
    """Package manage related functions"""
    @classmethod
    def ensure_config(cls, config: dict):
        """Ensure the config contains tool.start.dependencies and
        tool.start.dev-dependencies.

        Args:
            config: Config dict, parse from toml file
        """
        if "project" not in config:
            config["project"] = {"dependencies": []}
        if "tool" not in config:
            config["tool"] = {"start": {"dev-dependencies": []}}
        if "start" not in config["tool"]:
            config["tool"]["start"] = {"dev-dependencies": []}
        if not isinstance(config["project"]["dependencies"], list):
            Error("project.dependencies is not a list, start fix it.")
            config["project"]["dependencies"] = []
        if not isinstance(config["tool"]["start"]["dev-dependencies"], list):
            Error("tool.start.dev-dependencies is not a list, start fix it.")
            config["tool"]["start"]["dev-dependencies"] = []

    @classmethod
    def load_dependencies(cls, config_path: str) -> List[str]:
        """Try to load dependency list from the config path.

        Args:
            config_path: Path to the config file
        """
        if config_path.endswith(".toml"):
            with open(config_path, encoding="utf8") as f:
                config = rtoml.load(f)
                cls.ensure_config(config)
                return config["project"]["dependencies"]
        if config_path.endswith(".txt"):
            with open(config_path, encoding="utf8") as f:
                return f.read().splitlines()
        Error("Not found dependencies due to unsupported dependency file format")
        return []

    @classmethod
    def modify_dependencies(
        cls,
        method: Literal["add", "remove"],
        packages: Tuple,
        file: str,
        dev: bool = False
    ):
        """Change the dependencies in the specified file(Only support toml file).

        Args:
            method: "add" or "remove"
            packages: Packages to add or remove
            file: File name
            dev: Add packages as development dependency
        """
        if not cls.ensure_path(file):
            Error("No dependency file found")
            return

        with open(file, encoding="utf8") as f:
            config = rtoml.load(f)
            cls.ensure_config(config)

        if method == "add":
            dependencies: list = config["project"]["dependencies"] if not dev \
                else config["tool"]["start"]["dev-dependencies"]
            for package in packages:
                if package not in dependencies:
                    dependencies.append(package)
            dependencies.sort()
        elif method == "remove":
            for package in packages:
                if not dev and package in config["project"]["dependencies"]:
                    config["project"]["dependencies"].remove(package)
                if package in config["tool"]["start"]["dev-dependencies"]:
                    config["tool"]["start"]["dev-dependencies"].remove(package)

        with open(file, "w", encoding="utf8") as f:
            rtoml.dump(config, f)

    @classmethod
    def ensure_path(cls, basename: str, parent: int = 2) -> Optional[str]:
        """Find the file or folder from current path to parent directories.

        Args:
            basename: File or folder name
            parent: Parent directory depth
        """
        for i in range(parent, -1, -1):
            path = os.path.join(os.getcwd(), *[".."] * i, basename)
            if os.path.exists(path):
                return path
        return None

    @classmethod
    def find_executable(cls) -> str:
        """Find available executable in the system. If virtual environment
        was activated, return the interpreter path which is in VIRTUAL_ENV
        bin directory, else start will find .venv, .env as env_path. If not
        find any, return "python"
        """
        bin_path = "Scripts" if sys.platform.startswith("win") else "bin"
        if env_path := os.getenv("VIRTUAL_ENV"):
            return os.path.join(env_path, bin_path, "python")
        elif env_path :=(
                cls.ensure_path(".venv") or
                cls.ensure_path(".env")):
            Info(f"Found virtual environment '{env_path}' but was not"
                 "activated, packages was installed by this interpreter")
            display_activate_cmd(env_path)
            return os.path.join(env_path, bin_path, "python")
        return "python"


class PipManager:
    """Parse the pip output to get the install or uninstall information.

    Args:
        output: Raw subprocess.run output.
    """
    stdout: List[str]
    stderr: List[str]

    def __init__(self, executable: str):
        self.cmd = [executable, "-m", "pip"]

    def execute(self, cmd: List[str]):
        """Execute the pip command."""
        self.set_outputs(
            subprocess.run(cmd, capture_output=True)
        ).check_output()

    def install(self, packages: Sequence[str], upgrade: bool = False):
        """Install packages.

        Args:
            packages: Packages to install
            upgrade: Upgrade packages
        """
        cmd = self.cmd + ["install"]
        if upgrade:
            cmd.append("-U")
        cmd.extend(packages)
        self.execute(cmd)

    def uninstall(self, packages: Sequence[str]):
        """Uninstall packages.

        Args:
            packages: Packages to uninstall
        """
        cmd = self.cmd + ["uninstall", "-y"]
        cmd.extend(packages)
        self.execute(cmd)

    def set_outputs(self, output: subprocess.CompletedProcess):
        """Set the outputs that to be parse."""
        self.stdout = self.decode(
            output.stdout).strip().replace("\r", "").split("\n") \
            if output.stdout else []
        self.stderr = self.decode(
            output.stderr).strip().replace("\r", "").split("\n") \
            if output.stderr else []
        return self

    def decode(self, output: bytes):
        """Decode the output to utf8 or gbk."""
        try:
            return output.decode("utf8")
        except UnicodeDecodeError:
            return output.decode("gbk")

    def check_output(self):
        """Check if the pip install or uninstall is successful."""
        for line in self.stdout:
            line = line.strip()
            if line.startswith("Requirement already satisfied"):
                Warn(line)
            if line.startswith("Successfully"):
                Success(line)
        if self.stderr:
            Error("Install/Uninstall packages failed:")
            Detail("\n".join(self.stderr))


class ExtEnvBuilder(venv.EnvBuilder):
    """Extend environment builder to install packages.

    Args:
        packages: Packages to install after create the virtual environment
        force: Remove the existing virtual environment if it exists
        without_pip: Dont install pip in the virtual environment
        without_upgrade: Dont upgrade core package(pip & setuptools) and
            packages to install in the virtual environment
        without_system_packages: Dont give the virtual environment access
            to system packages
    """

    def __init__(
        self,
        packages: Tuple = (),
        force: bool = False,
        without_pip: bool = False,
        without_upgrade: bool = False,
        without_system_packages: bool = False,
    ):
        super().__init__(
            clear=force,
            system_site_packages=not without_system_packages,
            with_pip=not without_pip)
        self.packages = packages
        self.upgrade_packages = not without_upgrade

    def post_setup(self, context: SimpleNamespace):
        """Install and upgrade packages after created environment."""
        if self.with_pip and (self.upgrade_packages or self.packages):
            pip = PipManager(context.env_exe)
            if self.upgrade_packages:
                Info("Upgrading core packages...")
                pip.install(("pip", "setuptools"), upgrade=True)
            if self.packages:
                Info("Start installing packages...")
                pip.install(self.packages)

        display_activate_cmd(context.env_dir)