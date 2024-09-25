import os
import shutil
import unittest
from pathlib import Path
from tempfile import mkdtemp


class TestBase(unittest.TestCase):
    """Change the current working directory to a temporary directory before running each test."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cwd = Path.cwd()
        cls.tmp_dir = mkdtemp(prefix="start-test-")
        os.chdir(cls.tmp_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp_dir)
        os.chdir(cls.cwd)
