# Start

A python package manager based on pip and venv, use `pyproject.toml` instead of `requirements.txt`

## install

Install from github

```shell
>>> pip install https://github.com/Dragon-GCS/Start
```

> `start` is a default alias in **powershell**, so use **`Remove-Item alias:start -Force`** to remove alias before use `start`
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
    --force=FORCE
        Type: bool
        Remove the existing virtual environment if it exists
    --without_pip=WITHOUT_PIP
        Type: bool
        Default to install pip in the virtual environment, add "--without-pip" to skip this.
    --without_upgrade=WITHOUT_UPGRADE
        Type: bool
        Default to upgrade core package(pip & setuptools) and all packages to install in the
        virtual environment, add "--without-upgrade" to skip this.
    --without_system_packages=WITHOUT_SYSTEM_PACKAGES
        Type: bool
        Default to give the virtual environment access to system packages, add
        "--without-system-packages" to skip this.
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
    --force=FORCE
        Type: bool
        Remove the existing virtual environment if it exists
    --without_pip=WITHOUT_PIP
        Type: bool
        Default to install pip in the virtual environment, add "--without-pip" to skip this.
    --without_upgrade=WITHOUT_UPGRADE
        Type: bool
        Default to upgrade core package(pip & setuptools) and all packages to install in the
        virtual environment, add "--without-upgrade" to skip this.
    --without_system_packages=WITHOUT_SYSTEM_PACKAGES
        Type: bool
        Default to give the virtual environment access to system packages, add
        "--without-system-packages" to skip this.
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
```
