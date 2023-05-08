import os
import subprocess
import unittest
from test.utils import capture_output

from start import Start
from start.logger import Info, Warn
from start.manager import display_activate_cmd, try_git_init


class TestStart(unittest.TestCase):
    def setUp(self) -> None:
        self.env_dir = ".venv"
        if not os.path.isdir(".venv"):
            Start().init(vname=self.env_dir)

    def test_activate_cmd(self):
        if os.name == "nt":
            self.assertEqual(display_activate_cmd(self.env_dir), ".\\.venv\\Scripts\\activate")
            os.name = "unix"    # mock unix
        base_path = os.path.join(".", ".venv", "bin", "activate")
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

    def test_git_init(self):
        try:
            subprocess.check_output(["git", "--version"])
            has_git = True
        except FileNotFoundError:
            has_git = False

        if not has_git:
            with capture_output() as output:
                try_git_init()
            self.assertEqual(output.getvalue().strip(), repr(Warn("Git not found, skip git init.")))

        if os.path.exists(".git"):
            with capture_output() as output:
                try_git_init()
            self.assertEqual(
                output.getvalue().strip(), repr(Info("Git repository already exists."))
            )
            try:
                os.rename(".git", ".git.bak")
            except PermissionError:
                print("PermissionError: cannot rename .git to .git.bak for testing.")
                return

        with capture_output() as output:
            try_git_init()
        self.assertEqual(
            output.getvalue().strip(), repr(Info("Git repository initialized."))
        )

        os.rmdir(".git")
        if os.path.exists(".git.bak"):
            os.rename(".git.bak", ".git")
