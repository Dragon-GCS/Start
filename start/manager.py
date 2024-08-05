import contextlib
import os
import re
import sys
import time
import venv
from io import TextIOWrapper
from subprocess import PIPE, CalledProcessError, CompletedProcess, check_call, run
from tempfile import TemporaryFile
from threading import Thread
from types import SimpleNamespace
from typing import Dict, Generator, Iterable, List, Literal, Optional, Tuple

import rtoml
from typer import Argument, Option, Typer

from start.logger import Error, Info, Prompt, Success, Warn

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


def display_activate_cmd(env_dir: str, prompt: bool = True):
    """Display the activate command for the virtual environment.

    Args:
        env_dir (str): Path to the virtual environment directory
        prompt (bool): Whether to prompt the command
    Returns:
        cmd: The command to activate the virtual environment
    """
    active_scripts = {
        "bash": "activate",
        "zsh": "activate",
        "fish": "activate.fish",
        "csh": "activate.csh",
        "tcsh": "activate.csh",
        "Powershell": "Activate.ps1",
    }
    if shell := os.path.basename(os.getenv("SHELL", "")):
        bin_path = os.path.join(env_dir, "bin", active_scripts[shell])
    elif os.name == "nt":
        # Only support powershell on windows
        # Cmd has a conflict with start command
        bin_path = os.path.join(env_dir, "Scripts", active_scripts["Powershell"])
    else:
        Warn("Unknown shell, decide for yourself how to activate the virtual environment.")
        return ""

    active_cmd = os.path.abspath(bin_path)
    if not os.access(bin_path, os.X_OK):
        active_cmd = "source " + active_cmd
    if prompt:
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


@contextlib.contextmanager
def capture_output(verbose: bool = False) -> Generator[int | TextIOWrapper, None, None]:
    if not verbose:
        yield PIPE
        return

    stdout = TemporaryFile("w+", buffering=1, newline="\n")
    running = True

    def _read_output():
        # wait for the first data to read
        while not stdout.tell():
            time.sleep(0.1)
        ptr, _cur_ptr = 0, 0
        while running:
            _cur_ptr = stdout.tell()
            # wait for new data to read
            if _cur_ptr == ptr:
                time.sleep(0.1)
                continue
            # seek to the last read position
            stdout.seek(ptr)
            try:
                data = stdout.readline()
            except UnicodeDecodeError:
                # if decode failed, seek to the last read position
                # wait newline to be written and try to read again
                stdout.seek(ptr)
                continue
            print(data, end="")
            # ? the progress bar will by read twice without this
            if data.endswith("00:00\n"):
                ptr += len(data)
            ptr += len(data)
            stdout.seek(_cur_ptr)
        stdout.seek(ptr)
        print(stdout.read(), end="")

    t = Thread(target=_read_output)
    t.start()
    yield stdout  # type: ignore # return the file object type
    running = False
    t.join()


class PipManager:
    """Parse the pip output to get the install or uninstall information.

    Args:
        executable: The python executable path
        verbose: Whether to display the pip execution progress
    """

    stdout: List[str]
    stderr: List[str]
    return_code: int

    def __init__(self, executable: str, verbose: bool = False):
        self.cmd = [executable, "-m", "pip"]
        self.execu = executable
        self.verbose = verbose

    def execute(self, cmd: List[str]):
        """Execute the pip command."""
        cmd = self.cmd + cmd
        with capture_output(self.verbose) as stdout:
            try:
                output = run(cmd, text=True, stdout=stdout, stderr=stdout, check=True)
                # if verbose is True, the output has been displayed in capture_output
                if self.verbose and not isinstance(stdout, int):
                    stdout.seek(0)
                    output.stdout = stdout.read()
                self.set_outputs(output)
            except CalledProcessError as output:
                self.set_outputs(output)
        return self

    def install(self, *packages: str, upgrade: bool = False) -> List[str]:
        """Install packages.

        Args:
            packages: Packages to install
            upgrade: Upgrade packages
        Returns:
            packages: Success installed packages
        """
        if not packages:
            return []
        cmd = ["install"]
        if upgrade:
            cmd.append("-U")
        Info("Start install packages: " + ", ".join(packages))
        self.execute([*cmd, *packages]).show_output()

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
        self.execute(["uninstall", "-y", *packages]).show_output()
        return [*packages]

    def set_outputs(self, output: CompletedProcess | CalledProcessError):
        """Set the outputs that to be parse."""
        self.stdout = output.stdout.strip().split("\n") if output.stdout else []
        self.stderr = output.stderr.strip().split("\n") if output.stderr else []
        self.return_code = output.returncode
        return self

    def decode(self, output: bytes):
        """Decode the output to utf8 or gbk."""
        try:
            return output.decode("utf8")
        except UnicodeDecodeError:
            return output.decode("gbk")

    def show_output(self):
        """Display the pip command output"""
        # if verbose is True, the output has been displayed
        if self.verbose:
            return
        for line in self.stdout:
            line = line.strip()
            if line.startswith("Requirement already satisfied"):
                Warn(line)
            if line.startswith("Successfully"):
                Success(line)
        if self.stderr:
            Error("\n".join(self.stderr))

    def parse_output(self, output: str) -> List[str]:
        """Parse the output of pip to extract the installed package name."""
        output = output.strip()
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
        require: Dependency file name, toml file or plain text file
        force: Remove the existing virtual environment if it exists
        verbose: Display the pip command output
        without_pip: Dont install pip in the virtual environment
        without_upgrade: Dont upgrade core package(pip & setuptools) and
            packages to install in the virtual environment
        without_system_packages: Dont give the virtual environment access
            to system packages
        init_repo: Try to init a git repository in the parent directory
    """

    def __init__(
        self,
        packages: List[str] | None = None,
        require: str = "",
        force: bool = False,
        verbose: bool = False,
        without_pip: bool = False,
        without_upgrade: bool = False,
        without_system_packages: bool = False,
        init_repo: bool = True,
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
        self.init_repo = init_repo
        self.verbose = verbose

    def post_setup(self, context: SimpleNamespace):
        """Install and upgrade packages after created environment."""
        if self.with_pip and (self.upgrade_packages or self.packages):
            pip = PipManager(context.env_exe, self.verbose)
            if self.upgrade_packages:
                Info("Upgrading core packages...")
                pip.install("pip", "setuptools", upgrade=True)
            if self.packages:
                Info("Start installing packages...")
                pip.install(*self.packages)

        display_activate_cmd(context.env_dir)
        if self.init_repo:
            try_git_init(os.path.dirname(os.path.abspath(context.env_dir)))


class EnvManager:
    # load data directory, read from START_DATA_DIR or $HOME/.start
    _data_dir: str = os.getenv("START_DATA_DIR", os.path.expanduser("~/.start"))
    os.makedirs(_data_dir, exist_ok=True)

    @classmethod
    def is_env_dir(cls, path: str):
        """Check path is a virtual environment directory."""
        bin_dir_name = "Scripts" if sys.platform.startswith("win") else "bin"
        activate_script = os.path.join(path, bin_dir_name, "activate")
        return os.path.exists(activate_script) and os.path.isfile(activate_script)


env_typer = Typer(help="Manager environments.")


@env_typer.command()
def activate(env_name: str = Argument(help="Name for environment")):
    """Display the activate command for the virtual environment.

    Start will check following path to find the virtual environment:

    - `$START_DATA_DIR/<ENV_NAME>`
    - `$START_DATA_DIR/<ENV_NAME>/.venv`
    - `$START_DATA_DIR/<ENV_NAME>/.env`
    - `$START_DATA_DIR/<ENV_NAME>/venv`
    - `$(pwd)/<ENV_NAME>`
    - `$(pwd)/<ENV_NAME>/.venv`
    - `$(pwd)/<ENV_NAME>/.env`
    - `$(pwd)/<ENV_NAME>/venv`

    To activate on different shell, use following commands:

    - Powershell: Invoke-Expression (&start env activate <ENV_NAME>)
    - cmd: Not support due to the conflict of start
    - bash/zsh: eval "$(start env activate <ENV_NAME>)"
    - fish: start env activate <ENV_NAME>| source
    - csh/tcsh: eval `start env activate <ENV_NAME>`
    """
    for base_dir in (EnvManager._data_dir, os.getcwd()):
        for env in (".", *DEFAULT_ENV):
            env_path = os.path.join(base_dir, env_name, env)
            if EnvManager.is_env_dir(env_path):
                active_cmd = display_activate_cmd(env_path, prompt=False)
                print(active_cmd)
                return
    Error(f"Virtual environment {env_name} not found.")


@env_typer.command()
def create(
    env_name: str = Argument(help="Name of the virtual environment", show_default=False),
    packages: list[str] = Argument(
        None, help="Packages to install after create the virtual environment", show_default=False
    ),
    require: str = Option(
        "", "-r", "--require", help="Dependency file name. Toml file or plain text file"
    ),
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
        help="Upgrade core package(pip & setuptools) and all packages to install in the virtual environment",
    ),
    without_system_packages: bool = Option(
        False,
        "--without-system-packages/--with-system-packages",
        help="Give the virtual environment access to system packages",
    ),
):
    """Create a virtual environment and install specified packages."""

    env_path = os.path.join(EnvManager._data_dir, env_name)
    if os.path.exists(env_path) and not force:
        Error(f"Virtual environment {env_name} already exists," "use --force to override")
        return
    Info(f"Creating virtual environment: {env_name}({env_path})")
    packages = packages or []
    ExtEnvBuilder(
        packages=packages,
        require=require,
        force=force,
        verbose=verbose,
        without_pip=without_pip,
        without_upgrade=without_upgrade,
        without_system_packages=without_system_packages,
        init_repo=False,
    ).create(env_path)
    Success("Finish creating virtual environment.")


@env_typer.command(name="list")
def list_environments():
    """List all virtual environments."""

    for env in os.listdir(EnvManager._data_dir):
        env_path = os.path.abspath(os.path.join(EnvManager._data_dir, env))
        if os.path.isdir(env_path):
            Info(f"{env}({env_path})")
