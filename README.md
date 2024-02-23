# Start

A python package manager based on pip and venv, use `pyproject.toml` instead of `requirements.txt`

## install

Install from pypi

```shell
>>> pip install start-manager
```

Install from github

```shell
>>> pip install start@git+https://github.com/Dragon-GCS/Start
```

> `start` is a default alias in **powershell**, use **`Remove-Item alias:start -Force`** to remove alias before use `start`
>
> **Optional:** Add `Remove-Item alias:start -Force` in powershell profile

## Usage

### `start init`

```shell
SYNOPSIS
    start init <flags> [PACKAGES]...

DESCRIPTION
    Use current directory as the project name and create a new project at the current directory.

POSITIONAL ARGUMENTS
    PACKAGES
        Packages to install after create the virtual environment

FLAGS
    --vname=VNAME
        Type: str
        Name of the virtual environment, default is ".venv"
    --require=REQUIRE:
        Type: str
        Dependency file name. Toml file or plain text file.
    --force=FORCE
        Type: bool
        Remove the existing virtual environment if it exists
    --verbose=VERBOSE
        Type: bool
        Default: False
        Display install details
    --without_pip=WITHOUT_PIP
        Type: bool
        Default to install pip in the virtual environment, add "--without_pip" to skip this.
    --without_upgrade=WITHOUT_UPGRADE
        Type: bool
        Default to upgrade core package(pip & setuptools) and all packages to install in the
        virtual environment, add "--without_upgrade" to skip this.
    --with_template=WITH_TEMPLATE:
        Add "--with_template" to create template files
    --without_system_packages=WITHOUT_SYSTEM_PACKAGES
        Type: bool
        Default to give the virtual environment access to system packages, add
        "--without_system_packages" to skip this.
```

### `start new`

```shell
SYNOPSIS
    start new PROJECT_NAME <flags> [PACKAGES]...

DESCRIPTION
    Create a new project. Create a virtual environment and install specified packages.

POSITIONAL ARGUMENTS
    PROJECT_NAME
        Name of the project
    PACKAGES
        Packages to install after create the virtual environment

FLAGS
    --vname=VNAME
        Type: str
        Name of the virtual environment, default is ".venv"
    --require=REQUIRE:
        Type: str
        Dependency file name. Toml file or plain text file.
    --force=FORCE
        Type: bool
        Remove the existing virtual environment if it exists
    --verbose=VERBOSE
        Type: bool
        Default: False
        Display install details
    --without_pip=WITHOUT_PIP
        Type: bool
        Default to install pip in the virtual environment, add "--without_pip" to skip this.
    --without_upgrade=WITHOUT_UPGRADE
        Type: bool
        Default to upgrade core package(pip & setuptools) and all packages to install in the
        virtual environment, add "--without_upgrade" to skip this.
    --with_template=WITH_TEMPLATE:
        Add "--with_template" to create template files
    --without_system_packages=WITHOUT_SYSTEM_PACKAGES
        Type: bool
        Default to give the virtual environment access to system packages, add
        "--without_system_packages" to skip this.
    --verbose=VERBOSE
        Type: bool
        Default: False
        Display install details
```

### `start install`

```shell
SYNOPSIS
    start install <flags>

DESCRIPTION
    Install packages in specified dependency file.

FLAGS
    --dependency=DEPENDENCY
        Type: str
        Default: ''
        Dependency file name. If given a toml file, start will parse "project.dependencies",
        else start will parse each line as a package name to install. As default, if not found
        "pyproject.toml", start will try to find "requirements.txt" When virtual environment
        is not activated, start will try to find interpreter in .venv, .env orderly.
    --verbose=VERBOSE
        Type: bool
        Default: False
        Display install details
```

### `start add`

```shell
SYNOPSIS
    start add <flags> [PACKAGES]...

DESCRIPTION
    Install packages and add to the dependency file.

POSITIONAL ARGUMENTS
    PACKAGES

FLAGS
    --dev=DEV
        Type: bool
        Add packages as development dependency
    --dependency=DEPENDENCY
        Type: str
        Dependency file name, default is pyproject.toml (Only support toml file now). If
        file not exists, it will be create.
    --verbose=VERBOSE
        Type: bool
        Default: False
        Display install details
```

### `start remove`

```shell
SYNOPSIS
    start remove <flags> [PACKAGES]...

DESCRIPTION
    Uninstall packages and remove from the dependency file.

POSITIONAL ARGUMENTS
    PACKAGES

FLAGS
    --dev=DEV
        Type: bool
        Remove packages from development dependency
    --dependency=DEPENDENCY
        Type: str
        Dependency file name, default is pyproject.toml (Only support toml file now).
        If file not exists, it will be create.
    --verbose=VERBOSE
        Type: bool
        Default: False
        Display uninstall details
```

### `start show`

```shell
SYNOPSIS
    start show [PACKAGES]...

DESCRIPTION
    Same as "pip show" command.

POSITIONAL ARGUMENTS
    PACKAGES
        Packages to show
```

### `start list`

```shell
SYNOPSIS
    start list <flags>

DESCRIPTION
    Display all installed packages.

FLAGS
    --tree=TREE
        Type: bool
        Display installed packages in a tree structure
    --dep=DEP
        Type: bool
        Display installed packages in a dependency file
    --dev=DEV
        Type: bool
        Display installed packages in development dependency
    --dependency=DEPENDENCY
        Type: str
        Dependency file name, default is pyproject.toml (Only support toml file now).
        Only take effect when "dep" or "dev"  is True.
```

### `start env activate`

```shell
SYNOPSIS
    start env activate ENV_NAME

DESCRIPTION
    To activate on different shell, use following commands:
    - Powershell: Invoke-Expression (&start env activate <ENV_NAME>)
    - cmd: Not support due to the conflict of start
    - bash/zsh: eval "$(start env activate <ENV_NAME>)"
    - fish: start env activate <ENV_NAME>| source
    - csh/tcsh: eval `start env activate <ENV_NAME>`

POSITIONAL ARGUMENTS
    ENV_NAME
        Type: str
```

### `start env create`

```shell
SYNOPSIS
    start env create ENV_NAME <flags> [PACKAGES]...

DESCRIPTION
    Create a virtual environment and record it.

POSITIONAL ARGUMENTS
    ENV_NAME
        Type: str
        Name of the virtual environment
    PACKAGES
        Packages to install after create the virtual environment

FLAGS
    -r, --require=REQUIRE
        Type: str
        Default: ''
        Dependency file name. Toml file or plain text file.
    -f, --force=FORCE
        Type: bool
        Default: False
        Remove the existing virtual environment if it exists
    -v, --verbose=VERBOSE
        Type: bool
        Default: False
        Display the pip command output
    --without_pip=WITHOUT_PIP
        Type: bool
        Default: False
        Default to install pip in the virtual environment, add "--without-pip" to skip this.
    --without_upgrade=WITHOUT_UPGRADE
        Type: bool
        Default: False
        Default to upgrade core package(pip & setuptools) and all packages to install in the virtual environment, add "--without-upgrade" to skip this.
    --without_system_packages=WITHOUT_SYSTEM_PACKAGES
        Type: bool
        Default: False
        Default to give the virtual environment access to system packages, add "--without-system-packages" to skip this.
```

### `start env list`

```shell
SYNOPSIS
    start env list -

DESCRIPTION
    List all virtual environments.
```

## Changelog

### v0.5.3

- feat: add `--verbose` for `init`, `new`, `install`, `env create` command

### v0.5.2

- fix: Error when activate an relative path virtual environment

### v0.5.1

- fix: Not modify the dependency file when dependencies are not changed
- feat: Add "--verbose" to display install and uninstall details

### v0.5.0

- feat: add `start env` command to manager environments

### v0.4.7

- fix: correct the activate command

### v0.4.6

- feat: save prev dependencies when fix config file
- fix: error init when config.project.dependencies is an empty list

### v0.4.5

- fix: do nothing where no package to install
- feat: all create .gitignore where detect git

### v0.4.4

- fix: skip empty line in txt dependency file

### v0.4.3

- fix: catch error when install/uninstall package with pip

### v0.4.2

- fix: skip git init when repo exists
- feat: change prompt message for activate virtual environment

### v0.4.1

- fix: error display package name caused by str.rstrip remove the 'm' character

### v0.4

- feat: check if git available and init new project as a repo

### v0.3.4

- feat: replace without_template with with_template, default not to create template files
- fix: rename template folder `test` -> `tests`

### v0.3.3

- feat: add prompt message when start install package

### v0.3.2

- feat: add `--require` flag to install package by dependency file when init project

### v0.3.1

- feat: without-template exclude pyproject.toml

### v0.3

- add: `--skip-template` flag in `start new` and `start init`
- fix: activate command on unix platform

### v0.2.8

- fix: cant record package with special format
- fix: unexpected blank line in template
- fix: package name neat, error cmd in <list> command

### v0.2.7

- fix: add unexpected package to toml file
- refactor: remove useless argument in PipManager.execute
- refactor: rename PipManager.check_output() to show_output()

### v0.2.6

- fix: dependency file check error

### v0.2.5

- fix: Error adding package to toml file when package was not installed correctly
- fix: error parsing optional installed package name
- fix: error when not found packages
- fix: executable find order

### v0.2.4

- fix: bug when print some word start with 'm'
- fix: change all package name to lower

### v0.2.3

- fix: sys.executable as default interpreter

### v0.2.2

- fix: decode error of subprocess' output

### v0.2.1

- fix: wrong display of last branch of dependencies tree

### v0.2

- add: `start show` and `start relist` command
