import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from typer import Exit

from start.logger import Error
from start.utils import get_user_info

SETUP_PY = """
from setuptools import setup\n
if __name__ == '__main__':
    setup()
""".lstrip()
PYPROJECT_TOML = """
[build-system]
build-backend = "setuptools.build_meta"
requires = ["setuptools"]\n
[project]
name = "{project}"
version = "0.0.1"
dependencies = []
[[project.authors]]
name = "{username}"
email = "{email}"\n
[project.optional-dependencies]
dev = []\n
[tool.setuptools]
packages = ["{project}"]\n
""".lstrip()
MAIN_PY = """
import {}\n
if __name__ == '__main__':
    print("Hello, world!")
""".lstrip()
TEST_PY = """
import unittest\n
class Test{Camel}(unittest.TestCase):
    pass
""".lstrip()

TEMPLATES_DIR = Path(os.getenv("START_DATA_DIR", "~/.start")).expanduser() / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True, parents=True)


def copy_template(src: Path, dest: Path):
    """Copy files, folders, and symlinks from source to destination."""
    if not dest.exists():
        dest.mkdir(parents=True)

    for item in src.iterdir():
        if item.is_dir():
            copy_template(item, dest / item.name)
        elif not (dest_item := dest / item.name).exists():
            if item.is_symlink():
                dest_item.symlink_to(item.readlink())
            elif item.is_file():
                dest_item.write_bytes(item.read_bytes())


@dataclass
class Template:
    """Create project template with specified name.

    Args:
        project_name: Name of the project
        vname: Name of the virtual environment
        template_name: Name or git repo for the template
    """

    project_name: str
    template_name: str = ""

    def __post_init__(self):
        self.template_name = self.template_name.strip("/")
        if self.template_name.count("/") == 1:
            self.template_name = "https://github.com/" + self.template_name

    def create_default(self):
        """Default template for project, default structure is:
        project
        ├── {project_name}
        │   └── __init__.py
        ├── tests
        │   ├── __init__.py
        │   └── test_{project_name}.py
        ├── setup.py
        ├── main.py
        ├── README.md
        └── pyproject.toml
        """
        project_name = Path(self.project_name).absolute().name
        project_name = project_name.replace("-", "_").lower()

        Path(self.project_name, project_name).mkdir(exist_ok=True, parents=True)
        if not (init_file := Path(self.project_name, project_name, "__init__.py")).exists():
            init_file.touch()

        Path(self.project_name, "tests").mkdir(exist_ok=True, parents=True)
        if not (init_file := Path(self.project_name, "tests", "__init__.py")).exists():
            init_file.touch()
        if not (test_file := Path(self.project_name, "tests", f"test_{project_name}.py")).exists():
            test_file.write_text(
                TEST_PY.format(Camel="".join(w.capitalize() for w in project_name.split("_")))
            )

        if not (setup_file := Path(self.project_name, "setup.py")).exists():
            setup_file.write_text(SETUP_PY)
        if not (pyproject_file := Path(self.project_name, "pyproject.toml")).exists():
            username, email = get_user_info()
            pyproject_file.write_text(
                PYPROJECT_TOML.format(project=project_name, username=username, email=email)
            )
        if not (main_file := Path(self.project_name, "main.py")).exists():
            main_file.write_text(MAIN_PY.format(project_name))
        if not (readme_file := Path(self.project_name, "README.md")).exists():
            readme_file.touch()

    def create_by_local_template(self):
        """Create project template from local path."""
        if not (template_folder := TEMPLATES_DIR / self.template_name).exists():
            Error(f"Template '{self.template_name}' not found.")
            raise Exit(1)
        copy_template(template_folder, Path(self.project_name))

    def create_by_remote_template(self):
        try:
            subprocess.check_output(
                ["git", "clone", self.template_name, self.project_name],
                stderr=subprocess.STDOUT,
                encoding="utf-8",
            )
        except subprocess.CalledProcessError as e:
            Error(f"Error cloning template: {self.template_name}")
            Error(e.output.strip())
            raise Exit(1)

    def create(self):
        """Create project template at specified path.

        Args:
            path: Path to create the template
            skip_template: Skip template creation
        """
        if not self.template_name:
            self.create_default()
        elif self.template_name.startswith(("http", "git")) or self.template_name.endswith(".git"):
            self.create_by_remote_template()
        else:
            self.create_by_local_template()
