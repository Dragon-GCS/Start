import os

from start.logger import Warn


SETUP_PY = """
from setuptools import setup\n
if __name__ == '__main__':
    setup()
"""
PYPROJECT_TOML = """
[build-system]
build-backend = "setuptools.build_meta"
requires = ["setuptools"]\n
[project]
name = "{name}"
version = "0.0.1"\n
dependencies = []
[[project.authors]]
name = ""
email = "example@example.com"\n
[tool.setuptools]
packages = ["{name}"]\n
[tool.start]
dev-dependencies = []
"""
MAIN_PY = """
import {}\n
if __name__ == '__main__':
    print("Hello, world!")
"""
TEST_PY = """
import unittest\n
class Test{Camel}(unittest.TestCase):
    pass
"""


START_CONFIG_PATH = [
    os.path.join(os.path.expanduser("~"), ".start"),
    os.path.join(os.path.expanduser("~"), ".config", "start"),
]


class Template:
    def __init__(self, project_name: str):
        self.project_name = project_name

    @classmethod
    def write_file(cls, file_path: str, content: str):
        """Write content to file."""
        if not os.path.isfile(file_path):
            with open(file_path, "w", encoding="utf8") as f:
                f.write(content)
        else:
            Warn(f"File '{file_path}' already exists.")

    @classmethod
    def create_folder(cls, folder_path):
        """Create folder with examining if it exists."""
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
        else:
            Warn(f"Folder '{folder_path}' already exists.")

    def create_by_template(self):
        ...

    def create_default(self):
        """Default template for project."""
        project_name = self.project_name.replace("-", "_")

        self.create_folder(project_name)
        self.write_file(os.path.join(project_name, "__init__.py"), "")

        self.create_folder("test")
        self.write_file(os.path.join("test", "__init__.py"), "")
        self.write_file(
            os.path.join("test", "test_{}.py".format(project_name)),
            TEST_PY.format(
                Camel="".join(w.capitalize() for w in project_name.split("_")))
        )
        self.write_file("setup.py", SETUP_PY)
        self.write_file(
            "pyproject.toml", PYPROJECT_TOML.format(name=project_name))
        self.write_file("main.py", MAIN_PY.format(project_name))
        self.write_file("README.md", "")

    def create(self):
        """Create project template at specified path.

        Args:
            path: Path to create the template
        """
        current_dir = os.getcwd()

        if self.project_name == ".":
            self.project_name = os.path.basename(current_dir).lower()
        else:
            os.chdir(self.project_name)

        for config_path in START_CONFIG_PATH:
            if os.path.exists(os.path.join(config_path, "template")):
                self.create_by_template()
        else:
            self.create_default()

        os.chdir(current_dir)
