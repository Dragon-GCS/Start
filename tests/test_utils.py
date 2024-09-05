import os
import shutil
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from start.utils import display_activate_cmd, try_git_init


class TestStart(unittest.TestCase):
    def setUp(self) -> None:
        self.env_dir = ".venv"
        self.need_clean = False
        if not os.path.isdir(".venv"):
            # Start().init(vname=self.env_dir)
            self.need_clean = True

    def tearDown(self) -> None:
        if self.need_clean:
            shutil.rmtree(self.env_dir)

    def test_activate_cmd(self):
        cwd = os.getcwd()
        if os.name == "nt":
            self.assertEqual(
                display_activate_cmd(self.env_dir),
                os.path.join(cwd, ".venv\\Scripts\\Activate.ps1"),
            )
            os.name = "unix"  # mock unix
        base_path = os.path.join(cwd, ".venv", "bin", "activate")
        if not os.access(base_path, os.X_OK):
            base_path = "source " + base_path
        os.environ["SHELL"] = "/bin/bash"
        self.assertEqual(display_activate_cmd(self.env_dir), base_path)
        os.environ["SHELL"] = "/bin/zsh"
        self.assertEqual(display_activate_cmd(self.env_dir), base_path)
        os.environ["SHELL"] = "/bin/fish"
        self.assertEqual(display_activate_cmd(self.env_dir), base_path + ".fish")
        os.environ["SHELL"] = "/bin/csh"
        self.assertEqual(display_activate_cmd(self.env_dir), base_path + ".csh")
        os.environ["SHELL"] = ""
        self.assertEqual(display_activate_cmd(self.env_dir), "")

    @patch("start.logger")
    def test_git_init(self, mock_logger: MagicMock):
        try:
            subprocess.check_output(["git", "--version"])
            has_git = True
        except FileNotFoundError:
            has_git = False

        if has_git:
            try_git_init()
            mock_logger.Warn.assert_called_with("Git not found, skip git init.")
            return

        if os.path.exists(".git"):
            try_git_init()
            mock_logger.Warn.assert_called_with("Git repository already exists.")
        try:
            os.rename(".git", ".git.bak")
        except PermissionError:
            print("PermissionError: cannot rename .git to .git.bak for testing.")
            return

        os.rmdir(".git")
        if os.path.exists(".git.bak"):
            os.rename(".git.bak", ".git")
