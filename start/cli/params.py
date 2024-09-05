from typing import Annotated, Optional

from typer import Argument, Option

Dependency = Annotated[
    str,
    Option(
        "-d",
        "--dependency",
        help="Dependency file name. If given a toml file, start will parse "
        "'project.dependencies', else start will parse as requirements.txt. "
        "If toml file not exists, it will be created. "
        "If not given, start will find 'pyproject.toml' and 'requirements.txt'",
    ),
]
Group = Annotated[str, Option("-g", "--group", help="Specify group of dependencies to operate")]
EnvName = Annotated[str, Argument(help="Name of the virtual environment", show_default=False)]
Force = Annotated[
    bool,
    Option("-f", "--force", help="Remove the existing virtual environment if it exists"),
]
Packages = Annotated[
    Optional[list[str]], Argument(help="Packages to install or display", show_default=False)
]
ProjectName = Annotated[str, Argument(help="Name of the project", show_default=False)]
Require = Annotated[
    str, Option("-r", "--require", help="Dependency file name. Toml file or plain text file")
]
Template = Annotated[
    str,
    Option(
        "-t",
        "--template",
        help="Template to use for the project",
        show_default=False,
    ),
]
Tree = Annotated[
    bool, Option("-t", "--tree", help="Display installed packages in a tree structure")
]
VName = Annotated[str, Option("-n", "--vname", help="Name of the virtual environment")]
Verbose = Annotated[bool, Option("-v", "--verbose", help="Display install details")]
WithPip = Annotated[
    bool, Option("--with-pip/--without-pip", help="Install pip in the virtual environment")
]
WithoutUpgrade = Annotated[
    bool,
    Option(
        "--without-upgrade",
        help="Don't upgrade core package(pip & setuptools) and all packages to be installed in the virtual environment",
    ),
]
WithoutSystemPackages = Annotated[
    bool,
    Option(
        "--without-system-packages",
        help="Don't give the virtual environment access to system packages",
    ),
]
