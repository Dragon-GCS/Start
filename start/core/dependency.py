import re
from pathlib import Path
from typing import Any, Iterable, List, Literal

import rtoml
from typer import Exit

from start.core.config import DEFAULT_TOML_FILE_CONFIG
from start.logger import Error
from start.utils import update_config_with_default


class Dependency:
    """Parse the dependency string to name, extras, version and markers."""

    __slots__ = ("_raw", "name", "extra", "version", "markers")
    pkg_pattern = re.compile(
        r"""
    ^(?P<name>[\w\d_-]+)           # package name
    (\[(?P<extras>[\w\d_,\s]+)\])?  # extras option
    (\s*(?P<version_spec>[=><!~]+\s*[\w\d.*]+(,\s*([=><!~]+)\s*[\w\d.*]+)*))?   # version
    (\s*;\s*(?P<markers>.*))?      # markers
    $
    """,
        re.VERBOSE,
    )
    # https://pip.pypa.io/en/stable/topics/vcs-support/
    vcs_pattern = re.compile(
        r"""
    ((?P<pkg_name>[\w\d_-]+)@)?    # package name
    (?P<vcs>\w+)\+(?P<protocol>\w+)://  # vcs
    ((?P<username>[^/\\]+)(:(?P<password>.+))?@)?         # username
    (?P<url>[^@]*)                 # url
    /((?P<name>[\w\d_\-]+)(\.git)?)   # package name
    (@(?P<rev>.+))?        # revision
    """,
        re.VERBOSE,
    )

    def __init__(self, dep: str):
        self._raw = dep
        self.name = self.extra = self.version = self.markers = ""
        if match := self.pkg_pattern.match(dep):
            self.name = match.group("name").replace("_", "-")
            self.extra = match.group("extras") or ""
            self.version = match.group("version_spec") or ""
            self.markers = match.group("markers") or ""
        elif match := self.vcs_pattern.match(dep):
            self.name = match.group("pkg_name") or match.group("name")
            self.version = match.group("rev") or ""

    def __repr__(self):
        return self._raw

    def __eq__(self, other: Any):
        if isinstance(other, Dependency):
            return self.name == other.name
        elif isinstance(other, str):
            return str(self) == other
        return False

    def __hash__(self) -> int:
        return hash(self.name)


class DependencyManager:
    def __init__(self, config_file: str | Path):
        self.config_file = Path(config_file)
        self.is_toml_file = self.config_file.suffix == ".toml"
        self.config = DEFAULT_TOML_FILE_CONFIG
        if self.is_toml_file:
            self.config = update_config_with_default(rtoml.load(self.config_file), self.config)
        elif self.config_file.suffix == ".txt":
            with self.config_file.open(encoding="utf-8") as f:
                self.config["project"]["dependencies"] = [
                    line for _line in f if (line := _line.strip()) and line[0] not in "#-/!"
                ]
        else:
            Error(f"Unsupported file format: {config_file}")
            raise Exit(1)

        if not isinstance(self.config["project"]["dependencies"], list):
            Error("project.dependencies is not a list, start fix it.")
            self.config["project"]["dependencies_bak"] = self.config["project"]["dependencies"]
            self.config["project"]["dependencies"] = []
        self.project = self.config["project"]
        self._changed = False

    def packages(self, group: str = "") -> List[Dependency]:
        """
        Retrieve a list of dependencies, if group is specified, retrieve the dependencies in that group.
        Args:
            group (str): The group of dependencies to retrieve. Defaults to an empty string.
        Returns:
            List[Dependency]: A list of Dependency objects representing the retrieved dependencies.
        """

        packages = (
            self.project["dependencies"]
            if not group
            else self.project["optional-dependencies"].get(group, [])
        )
        return list(map(Dependency, packages))

    def modify_dependencies(
        self,
        method: Literal["add", "remove"],
        packages: Iterable[str],
        group: str = "",
        save: bool = False,
    ):
        """
        Modifies the dependencies of the project.
        Args:
            method (Literal["add", "remove"]): The method to use for modifying the dependencies.
                Must be either "add" or "remove".
            packages (Iterable[str]): The packages to add or remove from the dependencies.
            group (str): The group to modify. Defaults to "".
            save (bool): Whether to save the changes to the configuration file. Defaults to True.
        """
        if group and not self.is_toml_file:
            Error("Optional dependencies are only supported in TOML format.")
            raise Exit(1)

        if not group:
            packages_ref = self.project["dependencies"]
        elif group not in self.project["optional-dependencies"] and method == "remove":
            return
        else:
            packages_ref = self.project["optional-dependencies"][group]
        # convert package to pure name for lookup
        dependencies = {Dependency(p): p for p in packages_ref}

        _origin_package_num = len(packages_ref)
        if method == "add":
            packages_ref.extend(
                package for package in packages if Dependency(package) not in dependencies
            )
        elif method == "remove":
            for package in packages:
                if (dep := Dependency(package)) in dependencies:
                    packages_ref.remove(dependencies[dep])
        self._changed = _origin_package_num != len(packages_ref)
        packages_ref.sort()
        if save and self._changed:
            self.save()

    def add(self, packages: Iterable[str], group: str = "", save: bool = False):
        self.modify_dependencies("add", packages, group)

    def remove(self, packages: Iterable[str], group: str = "", save: bool = False):
        self.modify_dependencies("remove", packages, group)

    def save(self):
        """
        Saves the configuration to a file.
        If the configuration has not been changed, the method returns without saving.
        If the configuration is in TOML format, it is saved using the `rtoml.dump` function.
        If the configuration is not in TOML format, the dependencies are written to the file.
        After saving, the `_changed` flag is set to False.
        """

        if not self._changed:
            return
        if self.is_toml_file:
            rtoml.dump(self.config, self.config_file, pretty=True)
        else:
            with self.config_file.open("w", encoding="utf-8") as f:
                f.write("\n".join(self.project["dependencies"]))
        self._changed = False
