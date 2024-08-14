import contextlib
import os
import time
from io import TextIOWrapper
from subprocess import PIPE, CalledProcessError, CompletedProcess, run
from tempfile import TemporaryFile
from threading import Thread
from typing import Dict, Generator, List, Tuple

from start.logger import Error, Info, Success, Warn
from start.utils import neat_package_name

# subprocess use gbk in PIPE decoding and can't to change, due to
# UnicodeDecodeError when some package's meta data contains invalid characters.
# Refer: https://github.com/python/cpython/issues/50385
os.environ["PYTHONIOENCODING"] = "utf-8"

BRANCH = "├─"
END = "└─"
LINE = "│ "
INDENT = "  "


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
