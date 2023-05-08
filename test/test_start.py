import os
import unittest
from start.manager import display_activate_cmd
from start import Start

class TestStart(unittest.TestCase):
    def setUp(self) -> None:
        self.env_dir = ".venv"
        if not os.path.isdir(".venv"):
            Start().init(vname=self.env_dir)

    def test_activate_cmd(self):
        if os.name == "nt":
            self.assertEqual(display_activate_cmd(self.env_dir), ".\\.venv\\Scripts\\activate")
        os.environ["SHELL"] = "/bin/bash"
        self.assertEqual(display_activate_cmd(self.env_dir), "./.venv/bin/activate")
        os.environ["SHELL"] = "/bin/zsh"
        self.assertEqual(display_activate_cmd(self.env_dir), "./.venv/bin/activate")
        os.environ["SHELL"] = "/bin/fish"
        self.assertEqual(display_activate_cmd(self.env_dir), "./.venv/bin/activate.fish")
        os.environ["SHELL"] = "/bin/csh"
        self.assertEqual(display_activate_cmd(self.env_dir), "./.venv/bin/activate.csh")
        os.environ["SHELL"] = ""
        self.assertEqual(display_activate_cmd(self.env_dir), "")
