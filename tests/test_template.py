from pathlib import Path
from unittest.mock import ANY, patch

from start.core.template import Template, copy_template
from tests.base import TestBase


class TestTemplate(TestBase):
    def test_create_default(self):
        project_name = "test_project"
        Template(project_name, "").create()

        for file in (
            Path(project_name, project_name, "__init__.py"),
            Path(project_name, "tests", "__init__.py"),
            Path(project_name, "tests", f"test_{project_name}.py"),
            Path(project_name, "setup.py"),
            Path(project_name, "pyproject.toml"),
            Path(project_name, "main.py"),
            Path(project_name, "README.md"),
        ):
            with self.subTest(file=file):
                self.assertTrue(file.exists())

    def test_copy_template(self):
        Path("test_template", "folder1").mkdir(parents=True)

        Path("test_template", "file1").touch()
        Path("test_template", "folder1", "file2").write_bytes(b"file2")
        Path("test_template", "folder1", "file3").symlink_to("file2")

        copy_template(Path("test_template"), Path("dest_template"))

        self.assertTrue(Path("dest_template", "file1").exists())
        self.assertTrue(Path("dest_template", "folder1", "file2").exists())
        self.assertTrue(Path("dest_template", "folder1", "file3").exists())
        self.assertTrue(Path("dest_template", "folder1", "file3").is_symlink())
        self.assertEqual(
            Path("test_template", "folder1", "file2").read_bytes(),
            Path("dest_template", "folder1", "file2").read_bytes(),
        )
        self.assertEqual(Path("dest_template", "folder1", "file3").readlink(), Path("file2"))

    def test_create_by_local_template(self):
        project_name = "test_project"
        template_name = "local_template"
        template = Template(project_name, template_name)

        with (
            patch("start.core.template.Path.exists") as mock_exists,
            patch("start.core.template.copy_template") as mock_copy_template,
        ):
            mock_exists.return_value = True

            template.create_by_local_template()

            mock_copy_template.assert_called_once_with(
                Path("~/.start/templates/local_template").expanduser(), Path(project_name)
            )

    def test_create_by_remote_template(self):
        project_name = "test_project"
        template_name = "https://github.com/remote_template.git"
        template = Template(project_name, template_name)

        with patch("start.core.template.subprocess.check_output") as mock_check_output:
            template.create_by_remote_template()
            mock_check_output.assert_called_once_with(
                ["git", "clone", template_name, project_name],
                stderr=ANY,
                encoding="utf-8",
            )

    def test_create(self):
        project_name = "test_project"

        with (
            self.subTest(template=""),
            patch.object(Template, "create_default") as mock_create_default,
            patch.object(Template, "create_by_remote_template") as mock_create_by_remote_template,
            patch.object(Template, "create_by_local_template") as mock_create_by_local_template,
        ):
            Template(project_name, "").create()
            mock_create_default.assert_called_once()
            mock_create_by_local_template.assert_not_called()
            mock_create_by_remote_template.assert_not_called()

        with (
            self.subTest(template="local_template"),
            patch.object(Template, "create_default") as mock_create_default,
            patch.object(Template, "create_by_remote_template") as mock_create_by_remote_template,
            patch.object(Template, "create_by_local_template") as mock_create_by_local_template,
        ):
            Template(project_name, "local_template").create()
            mock_create_default.assert_not_called()
            mock_create_by_local_template.assert_called_once()
            mock_create_by_remote_template.assert_not_called()

        with (
            self.subTest(template="user/repo"),
            patch.object(Template, "create_default") as mock_create_default,
            patch.object(Template, "create_by_remote_template") as mock_create_by_remote_template,
            patch.object(Template, "create_by_local_template") as mock_create_by_local_template,
        ):
            Template(project_name, "user/repo").create()
            mock_create_default.assert_not_called()
            mock_create_by_local_template.assert_not_called()
            mock_create_by_remote_template.assert_called_once()

        with (
            self.subTest(template="https://gitea.com/user/repo"),
            patch.object(Template, "create_default") as mock_create_default,
            patch.object(Template, "create_by_remote_template") as mock_create_by_remote_template,
            patch.object(Template, "create_by_local_template") as mock_create_by_local_template,
        ):
            Template(project_name, "https://gitea.com/user/repo").create()
            mock_create_default.assert_not_called()
            mock_create_by_local_template.assert_not_called()
            mock_create_by_remote_template.assert_called_once()
