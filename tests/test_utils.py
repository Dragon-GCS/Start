import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from start.utils import display_activate_cmd, is_env_dir, try_git_init


class TestUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.env_dir = tempfile.mkdtemp()
        subprocess.check_call(["python", "-m", "venv", f"{cls.env_dir}", "--without-pip"])

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.env_dir):
            shutil.rmtree(cls.env_dir)

    def test_activate_cmd(self):
        if os.name == "nt":
            self.assertEqual(
                display_activate_cmd(self.env_dir),
                os.path.join(self.env_dir, "Scripts\\Activate.ps1"),
            )
            os.name = "unix"  # mock unix
        base_path = os.path.join(self.env_dir, "bin", "activate")
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

    @patch("start.utils.Warn")
    @patch("start.utils.Info")
    def test_git_init(self, mock_info: MagicMock, mock_warn: MagicMock):
        try:
            subprocess.check_output(["git", "--version"])
            has_git = True
        except FileNotFoundError:
            has_git = False

        if not has_git:
            mock_warn.assert_called_with("Git not found, skip git init.")
            return
        git_exists = Path(".git").exists()
        try_git_init(Path("."))

        if git_exists:
            mock_info.assert_called_with("Git repository already exists.")
        else:
            mock_info.assert_called_with("Git repository initialized.")

        if not git_exists:
            os.rmdir(".git")

    def test_is_env_dir(self):
        # Test when the path is a virtual environment directory
        self.assertTrue(is_env_dir(self.env_dir))

        # Test when the path does not exist
        self.assertFalse(is_env_dir("/path/to/nonexistent"))
