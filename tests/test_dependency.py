import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from start.core.config import DEFAULT_TOML_FILE_CONFIG
from start.core.dependency import Dependency, DependencyManager

cases = [
    ("SomeProject", "SomeProject", "", "", ""),
    ("SomeProject == 1.0", "SomeProject", "== 1.0", "", ""),
    ("SomeProject >= 1.0, < 2.0", "SomeProject", ">= 1.0, < 2.0", "", ""),
    ("SomeProject[foo, bar]", "SomeProject", "", "foo, bar", ""),
    ("SomeProject ~= 1.0", "SomeProject", "~= 1.0", "", ""),
    (
        "SomeProject == 1.0 ; python_version < '3.8'",
        "SomeProject",
        "== 1.0",
        "",
        "python_version < '3.8'",
    ),
    (
        "SomeProject ; sys_platform == 'win32'",
        "SomeProject",
        "",
        "",
        "sys_platform == 'win32'",
    ),
    (
        'SomeProject[security]>= 1.0, == 1.0.* ; python_version < "2.7"',
        "SomeProject",
        ">= 1.0, == 1.0.*",
        "security",
        'python_version < "2.7"',
    ),
]


class TestDependency(unittest.TestCase):
    def test_dependency(self):
        for case, *meta in cases:
            dep = Dependency(case)
            with self.subTest(case=case):
                self.assertEqual([dep.name, dep.version, dep.extra, dep.markers], meta)

    @classmethod
    def setUpClass(cls):
        with open("test.toml", "w") as f:
            f.write("[project]\ndependencies = []")

    @classmethod
    def tearDownClass(cls):
        os.remove("test.toml")

    def setUp(self):
        self.config_file = Path("test.toml")
        self.dependency_manager = DependencyManager(self.config_file)

    def test_packages(self):
        self.dependency_manager.project["dependencies"] = ["requests"]
        packages = self.dependency_manager.packages()
        self.assertEqual(packages, [Dependency("requests")])

    @patch("start.core.dependency.rtoml.load")
    def test_init_with_toml_file(self, mock_load: MagicMock):
        mock_load.return_value = {"project": {"dependencies": []}}
        dependency_manager = DependencyManager(self.config_file)
        self.assertEqual(dependency_manager.config_file, self.config_file)
        self.assertTrue(dependency_manager.is_toml_file)
        self.assertEqual(dependency_manager.config, DEFAULT_TOML_FILE_CONFIG)
        mock_load.assert_called_once_with(self.config_file)

    @patch("start.core.dependency.typer.Exit")
    @patch("start.core.dependency.Error")
    def test_init_with_unsupported_file_format(self, mock_error: MagicMock, mock_exit: MagicMock):
        config_file = "test.yaml"
        DependencyManager(config_file)
        mock_error.assert_called_once_with(
            f"Not found dependencies due to unsupported file format: {config_file}"
        )
        mock_exit.assert_called_once_with(1)

    def test_modify_dependencies_add(self):
        packages = ["package1 >= 1.0", "package2[extra]"]
        self.dependency_manager.modify_dependencies("add", packages)
        self.assertTrue(self.dependency_manager._changed)
        self.assertEqual(self.dependency_manager.project["dependencies"], packages)

    def test_modify_dependencies_remove(self):
        packages = ["package1 >= 1.0", "package2[extra]"]
        self.dependency_manager.modify_dependencies("add", packages)
        self.dependency_manager.modify_dependencies("remove", ["package1"])
        self.assertTrue(self.dependency_manager._changed)
        self.assertEqual(self.dependency_manager.project["dependencies"], ["package2[extra]"])

    @patch("pathlib.Path.open")
    @patch("start.core.dependency.rtoml.dump")
    def test_save(self, mock_dump: MagicMock, mock_open: MagicMock):
        self.dependency_manager._changed = True
        self.dependency_manager.save()
        mock_dump.assert_called_once_with(self.dependency_manager.config, self.config_file)

        self.dependency_manager.is_toml_file = False
        self.dependency_manager._changed = True
        self.dependency_manager.save()
        mock_open.assert_called_once_with("w", encoding="utf-8")
