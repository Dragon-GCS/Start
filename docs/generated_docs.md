# `Start`

Package manager based on pip and venv

**Usage**:

```console
$ Start [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `add`: Install packages and add to the dependency...
* `env`: Manager environments.
* `init`: Use current directory as the project name...
* `install`: Install packages in specified dependency...
* `list`: Display all installed packages.
* `new`: Create a new project and virtual...
* `remove`: Uninstall packages and remove from the...
* `show`: Show information about installed packages.

## `Start add`

Install packages and add to the dependency file.

**Usage**:

```console
$ Start add [OPTIONS] PACKAGES...
```

**Arguments**:

* `PACKAGES...`: Packages to install and record in the dependency file  [required]

**Options**:

* `-D, --dev`: Add packages as development dependency
* `-d, --dependency TEXT`: Dependency file name, default is pyproject.toml (Only support toml file now). If file not exists, it will be created.  [default: pyproject.toml]
* `-v, --verbose`: Display install details
* `--help`: Show this message and exit.

## `Start env`

Manager environments.

**Usage**:

```console
$ Start env [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `activate`: Display the activate command for the...
* `create`: Create a virtual environment and install...
* `list`: List all virtual environments.

### `Start env activate`

Display the activate command for the virtual environment.

Start will check following path to find the virtual environment:

- `$START_DATA_DIR/<ENV_NAME>`
- `$START_DATA_DIR/<ENV_NAME>/.venv`
- `$START_DATA_DIR/<ENV_NAME>/.env`
- `$START_DATA_DIR/<ENV_NAME>/venv`
- `$(pwd)/<ENV_NAME>`
- `$(pwd)/<ENV_NAME>/.venv`
- `$(pwd)/<ENV_NAME>/.env`
- `$(pwd)/<ENV_NAME>/venv`

To activate on different shell, use following commands:

- Powershell: Invoke-Expression (&start env activate <ENV_NAME>)
- cmd: Not support due to the conflict of start
- bash/zsh: eval "$(start env activate <ENV_NAME>)"
- fish: start env activate <ENV_NAME>| source
- csh/tcsh: eval `start env activate <ENV_NAME>`

**Usage**:

```console
$ Start env activate [OPTIONS] ENV_NAME
```

**Arguments**:

* `ENV_NAME`: Name for environment  [required]

**Options**:

* `--help`: Show this message and exit.

### `Start env create`

Create a virtual environment and install specified packages.

**Usage**:

```console
$ Start env create [OPTIONS] ENV_NAME [PACKAGES]...
```

**Arguments**:

* `ENV_NAME`: Name of the virtual environment  [required]
* `[PACKAGES]...`: Packages to install after create the virtual environment

**Options**:

* `-r, --require TEXT`: Dependency file name. Toml file or plain text file
* `-f, --force`: Remove the existing virtual environment if it exists
* `-v, --verbose`: Display install details
* `--without-pip / --with-pip`: Install pip in the virtual environment  [default: with-pip]
* `--without-upgrade / --with-upgrade`: Upgrade core package(pip & setuptools) and all packages to install in the virtual environment  [default: with-upgrade]
* `--without-system-packages / --with-system-packages`: Give the virtual environment access to system packages  [default: with-system-packages]
* `--help`: Show this message and exit.

### `Start env list`

List all virtual environments.

**Usage**:

```console
$ Start env list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `Start init`

Use current directory as the project name and create a new project at the current directory.

**Usage**:

```console
$ Start init [OPTIONS] [PACKAGES]...
```

**Arguments**:

* `[PACKAGES]...`: Packages to install after create the virtual environment

**Options**:

* `-r, --require TEXT`: Dependency file name. Toml file or plain text file
* `-v, --vname TEXT`: Name of the virtual environment  [default: .venv]
* `-f, --force`: Remove the existing virtual environment if it exists
* `-v, --verbose`: Display install details
* `--without-pip / --with-pip`: Install pip in the virtual environment  [default: with-pip]
* `--without-upgrade / --with-upgrade`: Upgrade core package(pip & setuptools) and all packages to be installed in the virtual environment  [default: with-upgrade]
* `--with-template / --without-template`: Create template files  [default: without-template]
* `--without-system-packages / --with-system-packages`: Give the virtual environment access to system packages  [default: with-system-packages]
* `--help`: Show this message and exit.

## `Start install`

Install packages in specified dependency file.

**Usage**:

```console
$ Start install [OPTIONS] [DEPENDENCY]
```

**Arguments**:

* `[DEPENDENCY]`: Dependency file name. If given a toml file, start will parse'project.dependencies', else start will parse each line asa package name to install. As default, if not found'pyproject.toml', start will try to find 'requirements.txt'When virtual environment is not activated, start will try tofind interpreter in .venv, .env orderly.

**Options**:

* `-v, --verbose`: Display install details
* `--help`: Show this message and exit.

## `Start list`

Display all installed packages.

**Usage**:

```console
$ Start list [OPTIONS]
```

**Options**:

* `-t, --tree`: Display installed packages in a tree structure
* `-D, --dev`: Display installed packages in development dependency
* `-d, --dependency TEXT`: Dependency file name
* `--help`: Show this message and exit.

## `Start new`

Create a new project and virtual environment, install the specified packages.

**Usage**:

```console
$ Start new [OPTIONS] PROJECT_NAME [PACKAGES]...
```

**Arguments**:

* `PROJECT_NAME`: Name of the project  [required]
* `[PACKAGES]...`: Packages to install after create the virtual environment

**Options**:

* `-r, --require TEXT`: Dependency file name. Toml file or plain text file
* `-v, --vname TEXT`: Name of the virtual environment  [default: .venv]
* `-f, --force`: Remove the existing virtual environment if it exists
* `-v, --verbose`: Display install details
* `--without-pip / --with-pip`: Install pip in the virtual environment  [default: with-pip]
* `--without-upgrade / --with-upgrade`: Upgrade core package(pip & setuptools) and all packages to be installed in the virtual environment  [default: with-upgrade]
* `--with-template / --without-template`: Create template files  [default: without-template]
* `--without-system-packages / --with-system-packages`: Give the virtual environment access to system packages  [default: with-system-packages]
* `--help`: Show this message and exit.

## `Start remove`

Uninstall packages and remove from the dependency file.

**Usage**:

```console
$ Start remove [OPTIONS] PACKAGES...
```

**Arguments**:

* `PACKAGES...`: Packages to uninstall and remove from the dependency file  [required]

**Options**:

* `-D, --dev`: Remove packages from development dependency
* `-d, --dependency TEXT`: Dependency file name, default is pyproject.toml (Only support toml file now). If file not exists, it will be created.  [default: pyproject.toml]
* `-v, --verbose`: Display uninstall details
* `--help`: Show this message and exit.

## `Start show`

Show information about installed packages.

**Usage**:

```console
$ Start show [OPTIONS] PACKAGES...
```

**Arguments**:

* `PACKAGES...`: Packages to show  [required]

**Options**:

* `--help`: Show this message and exit.
