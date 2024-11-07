import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer import Exit

from start.utils import _script_dir_name, display_activate_cmd, is_env_dir, try_git_init
from tests.base import TestBase


class TestUtils(TestBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.env_dir = Path(".venv")
        subprocess.check_call(["python", "-m", "venv", cls.env_dir, "--without-pip"])

    def test_activate_cmd(self):
        nt_activate_file = str((self.env_dir / _script_dir_name / "Activate.ps1").absolute())
        posix_activate_file = str((self.env_dir / _script_dir_name / "activate").absolute())
        if os.name == "nt":
            self.assertEqual(display_activate_cmd(self.env_dir), nt_activate_file)

        _shell = os.environ.get("SHELL", "")
        for shell, suffix in (
            ("/bin/bash", ""),
            ("/bin/zsh", ""),
            ("/bin/fish", ".fish"),
            ("/bin/csh", ".csh"),
        ):
            os.environ["SHELL"] = shell
            expected_cmd = posix_activate_file + suffix
            if os.name != "nt":
                expected_cmd = "source " + expected_cmd
            with self.subTest(shell=shell):
                self.assertEqual(display_activate_cmd(self.env_dir), expected_cmd)

        os.environ["SHELL"] = ""
        if os.name == "nt":
            self.assertEqual(display_activate_cmd(self.env_dir), nt_activate_file)
        else:
            with self.assertRaises(Exit):
                display_activate_cmd(self.env_dir)
        os.environ["SHELL"] = _shell

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

    def test_is_env_dir(self):
        # Test when the path is a virtual environment directory
        self.assertTrue(is_env_dir(self.env_dir))

        # Test when the path does not exist
        self.assertFalse(is_env_dir("/path/to/nonexistent"))
