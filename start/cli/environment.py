import os
from pathlib import Path
from subprocess import Popen

from typer import Context, Exit

from start.cli import params as _p
from start.core.config import DEFAULT_ENV
from start.core.env_builder import ExtEnvBuilder
from start.logger import Error, Info, Success
from start.utils import display_activate_cmd, is_env_dir

# load data directory, read from START_DATA_DIR or $HOME/.start
_data_dir = Path(os.getenv("START_DATA_DIR", "~/.start")).expanduser().absolute()
_data_dir.mkdir(exist_ok=True, parents=True)


def activate(env_name: _p.EnvName):
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
                raise Exit(0)
    Error(f"Virtual environment {env_name} not found.")
    raise Exit(1)


def create(
    ctx: Context,
    env_name: _p.EnvName,
    packages: _p.Packages = None,
    require: _p.Require = "",
    force: _p.Force = False,
    verbose: _p.Verbose = False,
    with_pip: _p.WithPip = True,
    without_upgrade: _p.WithoutUpgrade = False,
    without_system_packages: _p.WithoutSystemPackages = False,
):
    """Create a virtual environment and install specified packages."""

    env_path = _data_dir / env_name
    Info(f"Creating virtual environment: {env_name}({env_path})")
    ExtEnvBuilder(
        packages=packages,
        require=require,
        force=force,
        verbose=verbose,
        with_pip=with_pip,
        upgrade_core=not without_upgrade,
        system_site_packages=not without_system_packages,
        pip_args=ctx.meta["pip_args"],
    ).create(env_path)
    Success("Finish creating virtual environment.")


def list_environments():
    """List all virtual environments."""

    for env in _data_dir.iterdir():
        if is_env_dir(env):
            Info(f"{env.name}({env.absolute()})")


def run(commands: list[str], env: _p.VName = ""):
    """Run a command in the virtual environment."""
    if not env:
        # default to find environment in current directory
        for env in DEFAULT_ENV:
            if is_env_dir(env_path := env):
                break
        else:
            Error(
                "No virtual environment found. Use 'start init' to create a "
                "new environment on current directory."
            )
            raise Exit(1)
    # find environment in with specified name, or in data directory
    # env_path will be the first found path
    elif not (is_env_dir(env_path := env) or is_env_dir(env_path := _data_dir / env)):
        Error(
            f"Virtual environment {env} not found. Use 'start env create' to create a new environment."
        )
        raise Exit(1)

    active_cmd = display_activate_cmd(env_path, prompt=False)
    cmd = f"{active_cmd} && {' '.join(commands)}"
    if os.name == "nt":
        with Popen(["powershell.exe", "-c", cmd]) as proc:
            proc.communicate()
    else:
        if not (shell := os.getenv("SHELL")):
            Error("Unknown shell to run command.")
            raise Exit(1)
        os.execvp(shell, [shell, "-c", cmd])
