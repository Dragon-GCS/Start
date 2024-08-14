import os
import sys
from pathlib import Path
from typing import Iterable, List, Literal, Optional

import rtoml

from start.core.config import DEFAULT_ENV
from start.logger import Error, Info, Success
from start.utils import display_activate_cmd, neat_package_name


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
        if "dependencies" not in config["project"]:
            config["project"]["dependencies"] = []
        if "optional-dependencies" not in config["project"]:
            config["project"]["optional-dependencies"] = {"dev": []}
        if not isinstance(config["project"]["dependencies"], list):
            Error("project.dependencies is not a list, start fix it.")
            config["project"]["dependencies_bak"] = config["project"]["dependencies"]
            config["project"]["dependencies"] = []
        if not isinstance(config["project"]["optional-dependencies"].get("dev"), list):
            Error("project.optional-dependencies.dev is not a list, start fix it.")
            opt_deps = config["project"]["optional-dependencies"]
            opt_deps["dev_bak"], opt_deps["dev"] = opt_deps["dev"], []

    @classmethod
    def load_dependencies(
        cls, config_path: Path | str, dev: bool = False, neat: bool = False
    ) -> List[str]:
        """Try to load dependency list from the config path.

        Args:
            config_path: Path to the config file
            dev: Load dev-dependencies if True, otherwise load dependencies
            neat: remove '[]' in package name that was optional installed
        """
        if isinstance(config_path, str):
            config_path = Path(config_path)
        if config_path.suffix == ".toml":
            with open(config_path, encoding="utf8") as f:
                config = rtoml.load(f)
                cls.ensure_config(config)
                packages = config["project"]["dependencies"]
                if dev:
                    packages = config["project"]["optional-dependencies"]["dev"]
        elif config_path.suffix == ".txt":
            with open(config_path, encoding="utf8") as f:
                packages = [
                    line for _line in f if (line := _line.strip()) and line[0] not in "#-/!"
                ]
        else:
            Error(f"Not found dependencies due to unsupported file format: {config_path}")
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

        modified = False
        if method == "add":
            for package in packages:
                if package not in dependencies:
                    dependencies.append(package)
                    modified = True
            dependencies.sort()
        elif method == "remove":
            neat_dependencies = [neat_package_name(p) for p in dependencies]
            for package in packages:
                if package in neat_dependencies:
                    dependencies.pop(neat_dependencies.index(package))
                    neat_dependencies.remove(package)
                    modified = True
        if not modified:
            return
        with open(file_path, "w", encoding="utf8") as f:
            rtoml.dump(config, f, pretty=True)
        Success(f"Updated dependency file: {file_path}")

    @classmethod
    def ensure_path(cls, basename: str, parent: int = 2) -> Optional[Path]:
        """Find the file or folder from current path to parent directories.

        Args:
            basename: File or folder name
            parent: Parent directory depth
        Returns:
            the absolute path of the file or folder if found, otherwise None
        """
        path = Path.cwd()
        for _ in range(parent):
            executable = path / basename
            if executable.exists():
                return executable
            path = path.parent
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
        base_interpreter = Path(sys.executable).name
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
