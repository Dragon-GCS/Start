import os
import re
from pathlib import Path
from subprocess import CalledProcessError, check_call

from start.logger import Error, Info, Prompt, Warn


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


def display_activate_cmd(env_dir: Path, prompt: bool = True):
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
    if os.name == "nt":
        # Only support powershell on windows
        # Cmd has a conflict with start command
        bin_path = env_dir / "Scripts" / active_scripts["Powershell"]
    elif shell := Path(os.getenv("SHELL", "")).name:
        bin_path = env_dir / "bin" / active_scripts[shell]
    else:
        Warn("Unknown shell, decide for yourself how to activate the virtual environment.")
        return ""

    active_cmd = os.path.abspath(bin_path)
    if not os.access(bin_path, os.X_OK):
        active_cmd = "source " + active_cmd
    if prompt:
        Prompt("Run this command to activate the virtual environment: " + active_cmd)
    return active_cmd


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
