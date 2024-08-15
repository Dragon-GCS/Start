import os
import venv
from types import SimpleNamespace
from typing import List

from typer import Exit

from start.core.dependency import DependencyManager
from start.core.pip_manager import PipManager
from start.logger import Error, Info
from start.utils import display_activate_cmd, try_git_init


class ExtEnvBuilder(venv.EnvBuilder):
    """Extend environment builder to install packages.

    Args:
        packages: Packages to install after create the virtual environment
        require: Dependency file name, toml file or plain text file
        force: Remove the existing virtual environment if it exists
        verbose: Display the pip command output
        with_pip: Install pip in the virtual environment
        upgrade_core: Upgrade core package(pip & setuptools) and
            packages to install in the virtual environment
        system_site_packages: Dont give the virtual environment access
            to system packages
        init_repo: Try to init a git repository in the parent directory
        pip_args: Extra arguments to pass to pip command
    """

    def __init__(
        self,
        packages: List[str],
        require: str = "",
        force: bool = False,
        verbose: bool = False,
        with_pip: bool = True,
        upgrade_core: bool = False,
        system_site_packages: bool = False,
        init_repo: bool = True,
        pip_args: list[str] = [],
    ):
        super().__init__(clear=force, system_site_packages=system_site_packages, with_pip=with_pip)
        self.packages = packages or []
        if require:
            self.packages.extend(DependencyManager.load_dependencies(require))
        self.upgrade_core = upgrade_core
        self.init_repo = init_repo
        self.verbose = verbose
        self.pip_args = pip_args

    def ensure_directories(
        self, env_dir: str | bytes | os.PathLike[str] | os.PathLike[bytes]
    ) -> SimpleNamespace:
        if os.path.exists(env_dir) and not self.clear:
            Error(f"Virtual environment {env_dir} already exists, use --force to override")
            raise Exit(1)
        return super().ensure_directories(env_dir)

    def post_setup(self, context: SimpleNamespace):
        """Install and upgrade packages after created environment."""
        Info(context.env_exe)
        pip = PipManager(context.env_exe, self.verbose)
        if self.upgrade_core:
            Info("Upgrading core packages...")
            pip.install("pip", "setuptools", pip_args=["--upgrade"])

        if self.packages:
            Info("Start installing packages...")
            pip.install(*self.packages, pip_args=self.pip_args)
        Info(str(self.packages))

        display_activate_cmd(context.env_dir)
        if self.init_repo:
            try_git_init(os.path.dirname(os.path.abspath(context.env_dir)))