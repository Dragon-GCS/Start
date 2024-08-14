import os
import sys
from pathlib import Path

from typer import Argument, Option

from start.core.config import DEFAULT_ENV
from start.core.env_builder import ExtEnvBuilder
from start.logger import Error, Info, Success
from start.utils import display_activate_cmd

# load data directory, read from START_DATA_DIR or $HOME/.start
_data_dir = Path(os.getenv("START_DATA_DIR", "~/.start")).expanduser().absolute()
_data_dir.mkdir(exist_ok=True, parents=True)


def is_env_dir(path: Path):
    """Check path is a virtual environment directory."""
    bin_dir_name = "Scripts" if sys.platform.startswith("win") else "bin"
    return (path / bin_dir_name / "activate").is_file()


def activate(env_name: str = Argument(help="Name for environment")):
    """Display the activate command for the virtual environment.

    Start will check following path to find the virtual environment:

    - `$START_DATA_DIR/<ENV_NAME>`\n
    - `$START_DATA_DIR/<ENV_NAME>/.venv`\n
    - `$START_DATA_DIR/<ENV_NAME>/.env`\n
    - `$START_DATA_DIR/<ENV_NAME>/venv`\n
    - `$(pwd)/<ENV_NAME>`\n
    - `$(pwd)/<ENV_NAME>/.venv`\n
    - `$(pwd)/<ENV_NAME>/.env`\n
    - `$(pwd)/<ENV_NAME>/venv`\n


    To activate on different shell, use following commands:

    - Powershell: Invoke-Expression (&start env activate <ENV_NAME>)\n
    - cmd: Not support due to the conflict of start\n
    - bash/zsh: eval "$(start env activate <ENV_NAME>)"\n
    - fish: start env activate <ENV_NAME>| source\n
    - csh/tcsh: eval \\`start env activate <ENV_NAME>\\`\n
    """
    for base_dir in (_data_dir, Path.cwd()):
        for env in (".", *DEFAULT_ENV):
            env_path = base_dir / env_name / env
            if is_env_dir(env_path):
                active_cmd = display_activate_cmd(env_path, prompt=False)
                print(active_cmd)
                return
    Error(f"Virtual environment {env_name} not found.")


def create(
    env_name: str = Argument(help="Name of the virtual environment", show_default=False),
    packages: list[str] = Option(
        None,
        "-p",
        "--packages",
        help="Packages to install after create the virtual environment",
        show_default=False,
    ),
    require: str = Option(
        "", "-r", "--require", help="Dependency file name. Toml file or plain text file"
    ),
    force: bool = Option(
        False, "-f", "--force", help="Remove the existing virtual environment if it exists"
    ),
    verbose: bool = Option(False, "-v", "--verbose", help="Display install details"),
    with_pip: bool = Option(
        True, "--with-pip/--without-pip", help="Install pip in the virtual environment"
    ),
    without_upgrade: bool = Option(
        False,
        "--without-upgrade",
        help="Don't upgrade core package(pip & setuptools) and all packages to be installed in the virtual environment",
    ),
    without_system_packages: bool = Option(
        False,
        "--without-system-packages",
        help="Don't give the virtual environment access to system packages",
    ),
):
    """Create a virtual environment and install specified packages."""

    env_path = os.path.join(_data_dir, env_name)
    Info(f"Creating virtual environment: {env_name}({env_path})")
    ExtEnvBuilder(
        packages=packages,
        require=require,
        force=force,
        verbose=verbose,
        with_pip=with_pip,
        without_upgrade=without_upgrade,
        without_system_packages=without_system_packages,
        init_repo=False,
    ).create(env_path)
    Success("Finish creating virtual environment.")


def list_environments():
    """List all virtual environments."""

    for env in _data_dir.iterdir():
        if is_env_dir(env):
            Info(f"{env.name}({env.absolute()})")
