import os
import shutil
import unittest
from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import MagicMock, call, patch

from typer.testing import CliRunner

from start.cli import app
from start.core.dependency import Dependency

test_project = "test_project"
test_package = "pip-install-test"
test_env = ".test_env"


class TestBase(unittest.TestCase):
    """Change the current working directory to a temporary directory before running each test."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cwd = Path.cwd()
        cls.runner = CliRunner()
        cls.tmp_dir = mkdtemp()
        os.chdir(cls.tmp_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp_dir)
        os.chdir(cls.cwd)

    def invoke(self, *args, **kwargs):
        return self.runner.invoke(app, *args, **kwargs)


class TestProject(TestBase):
    @patch("start.core.env_builder.Error")
    @patch("start.cli.project.Info")
    @patch("start.cli.project.Success")
    def test_new(self, mock_success: MagicMock, mock_info: MagicMock, mock_error: MagicMock):
        self.invoke(["new", test_project, test_package, "-n", test_env])
        mock_info.assert_called_with(f"Start creating project: {test_project}")
        mock_success.assert_has_calls(
            [call("Finish creating virtual environment."), call("Finish creating project.")]
        )
        env_dir = Path(test_project, test_env)
        self.assertTrue(env_dir.is_dir())
        self.assertTrue(
            list(env_dir.glob(f'lib/python*/site-packages/{test_package.replace("-", "_")}*'))
        )
        result = self.invoke(["new", test_project, "-n", test_env])
        self.assertNotEqual(result.exit_code, 0)
        mock_error.assert_called_with(
            f"Virtual environment {env_dir.resolve()} already exists, use --force to override"
        )

    @patch("start.cli.project.DependencyManager")
    @patch("start.cli.project.PipManager")
    def test_install(self, mock_pip_manager: MagicMock, mock_dependency_manager: MagicMock):
        import os

        Path(test_project).mkdir()
        os.chdir(test_project)

        mock_dependency_manager.return_value.packages.return_value = [test_package]
        dep_file = Path("pyproject.toml").resolve()
        dep_file.write_text(f"[project]\ndependencies = [{test_package}]")
        self.invoke(["install"])
        mock_dependency_manager.assert_called_once_with(dep_file)
        mock_pip_manager.assert_called_with(verbose=False)
        mock_pip_manager.return_value.install.assert_called_once_with(test_package, pip_args=[])


class TestModify(TestBase):
    def setUp(self) -> None:
        super().setUp()
        self.dep_file = Path("requirements.txt")
        self.dep_file.write_text("")

    @patch("start.cli.modify.DependencyManager")
    @patch("start.cli.modify.PipManager")
    def test_modify_add(self, mock_pip_manager, mock_dependency_manager):
        mock_pip = mock_pip_manager.return_value
        mock_dm = mock_dependency_manager.return_value

        packages = ["package1", "package2"]
        group = "test_group"
        pip_args = ["--arg1", "--arg2"]

        for method, mock_method in (("add", mock_pip.install), ("remove", mock_pip.uninstall)):
            with self.subTest(method=method):
                self.invoke([method, *packages, "-g", group, "-d", self.dep_file, *pip_args, "-v"])

                mock_pip_manager.assert_called_with(verbose=True)
                mock_method.assert_called_with(*packages, pip_args=pip_args)
                mock_dependency_manager.assert_called_with(str(self.dep_file))
                mock_dm.modify_dependencies.assert_called_with(
                    method=method,
                    packages=mock_method.return_value,
                    group=group,
                    save=True,
                )


class TestInspect(TestBase):
    @patch("start.cli.inspect.PipManager")
    def test_show_packages(self, mock_pip_manager: MagicMock):
        mock_pip = mock_pip_manager.return_value

        result = self.invoke(["show", "package1", "package2"])
        self.assertEqual(result.exit_code, 0)
        mock_pip.execute.assert_called_with(["show", "package1", "package2"])

    @patch("start.cli.inspect.Detail")
    @patch("start.cli.inspect.PipManager")
    def test_list_packages(self, mock_pip_manager: MagicMock, mock_detail: MagicMock):
        mock_packages = ["package1", "package2"]
        mock_pip = mock_pip_manager.return_value
        mock_pip.execute.return_value.parse_list_output.return_value = mock_packages

        result = self.invoke(["list"])

        self.assertEqual(result.exit_code, 0)
        mock_pip.execute.assert_called_with(["list"])
        mock_pip.execute.return_value.parse_list_output.assert_called_once()
        mock_detail.assert_called_with("\n".join("- " + package for package in mock_packages))

    @patch("start.cli.inspect.PipManager")
    def test_list_packages_with_tree(self, mock_pip_manager: MagicMock):
        mock_pip = mock_pip_manager.return_value
        mock_pip.execute.return_value.parse_list_output.return_value = ["package1", "package2"]
        mock_pip.analyze_packages_require.return_value = [
            {"package1": ["dep1"]},
            {"package2": ["dep2"]},
        ]
        mock_pip.generate_dependency_tree.return_value = [
            ("package1", "tree_string1"),
            ("package2", "tree_string2"),
        ]

        self.invoke(["list", "-t"])

        mock_pip.execute.assert_called_with(["list"])
        mock_pip.execute.return_value.parse_list_output.assert_called_once()
        mock_pip.analyze_packages_require.assert_called_with("package1", "package2")
        mock_pip.generate_dependency_tree.assert_called()

    @patch("start.cli.inspect.ensure_path")
    def test_dependency_file_not_found(self, mock_ensure_path: MagicMock):
        filename = "nonexistent_file.toml"
        mock_ensure_path.return_value = None
        result = self.invoke(["list", "-d", filename])
        self.assertEqual(result.exit_code, 1)
        mock_ensure_path.assert_called_with(filename)

    @patch("start.cli.inspect.DependencyManager")
    @patch("start.cli.inspect.ensure_path")
    def test_list_packages_with_dependency(
        self, mock_ensure_path: MagicMock, mock_dependency_manager: MagicMock
    ):
        test_file = "test.toml"
        mock_ensure_path.return_value = test_file
        mock_dm = mock_dependency_manager.return_value
        mock_dm.packages.return_value = [Dependency("package1"), Dependency("package2")]

        with self.subTest(test="list without group"):
            result = self.invoke(["list", "-d", test_file])
            self.assertEqual(result.exit_code, 0)
            mock_ensure_path.assert_called_with(test_file)
            mock_dependency_manager.assert_called_with(test_file)
            mock_dm.packages.assert_called_with("")

        with self.subTest(test="list with group"):
            result = self.invoke(["list", "-d", test_file, "-g", "test_group"])
            self.assertEqual(result.exit_code, 0)
            mock_ensure_path.assert_called_with(test_file)
            mock_dependency_manager.assert_called_with(test_file)
            mock_dm.packages.assert_called_with("test_group")


class TestEnvironmentCreate(TestBase):
    def setUp(self) -> None:
        from start.cli import environment

        environment._data_dir = Path(self.tmp_dir)

    @patch("start.cli.environment.Info")
    @patch("start.cli.environment.Success")
    def test_create_environment(self, mock_success, mock_info):
        env_name = "test_env"
        pip_args = ["--upgrade"]

        result = self.invoke(["env", "create", env_name, test_package, "--without-pip", *pip_args])
        self.assertEqual(result.exit_code, 0)
        env_path = Path(self.tmp_dir, "test_env").absolute()
        mock_info.assert_called_with(f"Creating virtual environment: test_env({str(env_path)})")
        mock_success.assert_called_with("Finish creating virtual environment.")
        self.assertTrue(env_path.is_dir())

        with self.subTest(test="Test list environments"):
            result = self.invoke(["env", "list"])
            self.assertEqual(result.exit_code, 0)
            mock_info.assert_called_with(f"{env_name}({env_path})")

        with self.subTest(test="Test activate command"):
            result = self.invoke(["env", "activate", env_name])
            self.assertEqual(result.exit_code, 0)

        with self.subTest(test="Test activate unknown environment"):
            result = self.invoke(["env", "activate", "nonexistent_env"])
            self.assertNotEqual(result.exit_code, 0)
