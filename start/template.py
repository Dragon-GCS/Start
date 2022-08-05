import os

from .color import Green, Red


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


class Template:
    # :TODO skip existing file
    # :TODO add user template support
    def __init__(self, project_name: str):
        self.project_name = project_name

    def create_by_template(self):
        ...

    def create_default(self):
        project_name = self.project_name.replace("-", "_")
        os.makedirs(project_name, exist_ok=True)
        open(os.path.join(project_name, "__init__.py"), "w").close()
        os.makedirs("test", exist_ok=True)
        open(os.path.join("test", "__init__.py"), "w").close()
        with open(os.path.join("test", f"test_{project_name}.py"), "w") as f:
            f.write(TEST_PY.format(
                Camel="".join(w.capitalize() for w in project_name.split("_"))
            ))
        with open("setup.py", "w", encoding="utf8") as f:
            f.write(SETUP_PY)
        with open("pyproject.toml", "w", encoding="utf8") as f:
            f.write(PYPROJECT_TOML.format(name=project_name))
        with open("main.py", "w", encoding="utf8") as f:
            f.write(MAIN_PY.format(project_name))

        open("README.md", "w", encoding="utf8").close()

    def create(self):
        """Create project template at specified path.

        Args:
            path: Path to create the template
        """
        print(Green("Creating project files."))
        current_dir = os.getcwd()
        os.chdir(self.project_name)
        if os.path.exists("~/.start/template"):
            self.create_by_template()
        else:
            self.create_default()
        os.chdir(current_dir)
        print(Green("Finish creating project files."))


if __name__ == "__main__":
    ...
