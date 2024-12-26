import os
import sys
import sysconfig
from pathlib import Path
from subprocess import CalledProcessError, check_call, check_output
from typing import Optional

from typer import Exit

from start.core.config import DEFAULT_ENV
from start.logger import Error, Info, Prompt, Warn

_script_dir_name = Path(sysconfig.get_path("scripts")).name


def display_activate_cmd(env_dir: Path | str, prompt: bool = True) -> str:
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
    script_dir = Path(env_dir, _script_dir_name)
    shell = Path(os.getenv("SHELL", "")).name
    if not shell and os.name == "nt":
        shell = "Powershell"
    if not shell:
        Warn("Unknown shell, decide for yourself how to activate the virtual environment.")
        raise Exit(1)
    bin_path = script_dir / active_scripts[shell]
    active_cmd = str(bin_path.absolute())
    if os.name != "nt":
        active_cmd = "source " + active_cmd
    if prompt:
        Prompt("Run this command to activate the virtual environment: " + active_cmd)
    return active_cmd


def try_git_init(repo_dir: Path):
    """Try to init a git repository in repo_dir"""
    if (repo_dir / ".git").exists():
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


def get_user_info() -> tuple[str, str]:
    """Get user info from git config"""
    try:
        user_name = check_output(["git", "config", "user.name"]).decode("utf-8").strip()
        user_email = check_output(["git", "config", "user.email"]).decode("utf-8").strip()
        return user_name, user_email
    except (OSError, CalledProcessError):
        return "", ""


def update_config_with_default(config: dict, default: dict):
    """
    Update the given configuration dictionary with default values.

    Args:
        config (dict): The configuration dictionary to be updated.
        default (dict): The dictionary containing default values.
    """
    for key, value in default.items():
        if key not in config:
            config[key] = value
        elif isinstance(value, dict):
            update_config_with_default(config[key], value)
    return config


def ensure_path(basename: str, parent: int = 2) -> Optional[Path]:
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


def find_executable() -> str:
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
        if env_path := ensure_path(path):
            Info(
                f"Found virtual environment '{env_path}' but was not "
                "activated, packages was installed by this interpreter"
            )
            display_activate_cmd(env_path)
            return os.path.join(env_path, bin_dir, base_interpreter)
    return base_interpreter


def is_env_dir(path: Path | str):
    """Check path is a virtual environment directory."""
    return Path(path, _script_dir_name, "activate").is_file()
