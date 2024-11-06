import os
import re
from functools import cached_property
from subprocess import PIPE, Popen, check_output
from threading import Lock, Thread
from typing import Dict, Generator, List, Optional, Tuple

from start.core.dependency import Dependency
from start.logger import Error, Info, Success, Warn
from start.utils import find_executable

# subprocess use gbk in PIPE decoding and can't to change, due to
# UnicodeDecodeError when some package's meta data contains invalid characters.
# Refer: https://github.com/python/cpython/issues/50385
os.environ["PYTHONIOENCODING"] = "utf-8"

BRANCH = "├─"
END = "└─"
LINE = "│ "
INDENT = "  "


class PipManager:
    """Parse the pip output to get the install or uninstall information.

    Args:
        executable: The python executable path
        verbose: Whether to display the pip execution progress
    """

    stdout: List[str]
    stderr: List[str]
    return_code: int

    def __init__(self, executable: str | None = None, verbose: bool = False):
        if not executable:
            executable = find_executable()

        self.cmd = [executable, "-m", "pip"]
        self.execu = executable
        self.verbose = verbose
        if self.verbose and (not self.version or self.version[0] < 24):
            Warn("Option '--verbose' is only supported in pip version >= 24")
            self.verbose = False

    @cached_property
    def version(self) -> Optional[tuple[int, int]]:
        """Get the pip version."""
        output = check_output(self.cmd + ["--version"], text=True)
        if _match := re.search(r"(\d+)\.(\d+)(\.(\d+))?", output):
            return int(_match.group(1)), int(_match.group(2))
        return None

    def execute(self, cmd: List[str]):
        """Execute the pip command."""
        cmd = self.cmd + cmd
        with Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True) as process:
            if self.verbose:
                self.capture_outputs(process)
            else:
                stdout, stderr = process.communicate()
                self.stdout = stdout.strip().split("\n")
                self.stderr = stderr.strip().split("\n")
        self.return_code = process.returncode
        return self

    def install(self, *packages: str, pip_args: list[str]) -> List[str]:
        """Install packages.

        Args:
            packages: Packages to install
            upgrade: Upgrade packages
        Returns:
            packages: Success installed packages
        """
        if not packages:
            return []
        if self.verbose and not any(arg.startswith("--progress-bar") for arg in pip_args):
            pip_args.append("--progress-bar=raw")
        Info("Start install packages: " + ", ".join(packages))
        self.execute(["install", *packages, *pip_args]).show_output()

        installed_packages = set(
            package for line in self.stdout for package in self.parse_output(line)
        )
        return [package for package in packages if Dependency(package).name in installed_packages]

    def uninstall(self, *packages: str, pip_args: list[str]) -> List[str]:
        """Uninstall packages.

        Args:
            packages: Packages to uninstall
        Returns:
            packages: Success uninstalled packages
        """
        if not any(arg in ("-y", "--yes") for arg in pip_args):
            pip_args.append("-y")
        self.execute(["uninstall", *packages, *pip_args]).show_output()
        return [*packages]

    def capture_outputs(self, process: Popen):
        """Set the outputs that to be parse.
        Thanks to StackOverflow:
            https://stackoverflow.com/questions/2715847/read-streaming-input-from-subprocess-communicate/17698359
        """

        self.stdout, self.stderr = [], []
        _lock = Lock()
        assert process.stdout and process.stderr, "stdout and stderr should be set here"

        def read_stdout():
            from rich.progress import Progress

            assert process.stdout is not None
            # wait for the first data to read
            current_task = None
            with Progress() as progress:
                for line in process.stdout:
                    if match := re.match(r"Progress (\d+) of (\d+)", line):
                        if current_task is None:
                            current_task = progress.add_task(
                                description="\t", total=int(match.group(2))
                            )
                        progress.update(current_task, completed=int(match.group(1)))
                    else:
                        if current_task is not None:
                            progress.remove_task(current_task)
                            current_task = None
                        with _lock:
                            print(line, end="")
                        self.stdout.append(line.strip())

        # Guess stdout and stderr will close  together when the process is closed
        # So don't need to join this thread here
        Thread(target=read_stdout).start()

        for line in process.stderr:
            line = line.strip()
            with _lock:
                Error(line)
            self.stderr.append(line)

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
                name = Dependency(line.lstrip("Name:").strip()).name
            if line.startswith("Requires") and name:
                requires = line.lstrip("Requires:").strip().split(", ")
                packages_require[name] = [Dependency(r).name for r in requires if r]

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
