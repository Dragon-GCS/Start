import os
import sys
import subprocess
import time
from argparse import Namespace
from platform import system


def start(args: Namespace):
    default_packages = os.path.dirname(__file__) + "/default_packages.txt"
    # 删除默认安装的包
    if args.remove_default:
        os.remove(default_packages)
    # 保存需要默认安装的包至文件中
    if args.default:
        with open(default_packages, "w") as f:
            f.writelines(map(lambda pack: pack + '\n', args.default))

    # 虚拟环境位置
    env_dir = os.path.join(args.project_name, args.vname)

    # 启动虚拟环境命令
    if system() == "Windows":
        activate_cmd = os.path.abspath(os.path.join(
            env_dir, "Scripts", "activate[.ps1|.bat]"))
        interpreter_dir = "Scripts"
    else:
        activate_script = os.path.abspath(
            os.path.join(env_dir, "bin", "activate"))
        activate_cmd = " ".join(["source", activate_script])
        interpreter_dir = "bin"

    # 创建虚拟环境命令
    venv_cmd = [sys.executable, "-m", "venv", env_dir]
    # 使用虚拟环境解释器启动pip
    pip_cmd = [os.path.abspath(os.path.join(env_dir,
                                            interpreter_dir,
                                            os.path.basename(sys.executable))),
               "-m", "pip", "install"]

    # 添加默认安装包
    if os.path.isfile(default_packages):
        with open(default_packages) as f:
            args.package.extend(f.readlines())

    options = []
    # 安装指定包
    if args.package:
        options.extend(args.package)

    # 使用文件安装包
    if args.requirement:
        options.extend(["-r", args.requirement])

    # 虚拟环境检查
    if os.path.isdir(env_dir):
        print(f"File '{env_dir}' was already exists, ", end="")
        if args.force:
            print("it will be removed")
            venv_cmd.append("--clear")
        else:
            print("Add '-f' or '--force'to remove the old environment")
            print("Or activate the existed virtual environment by the following command:")
            exit(f"'{activate_cmd}'")

    # 启动安装
    try:
        print(
            f"Creating virtual environment as folder: {os.path.abspath(args.project_name)}")
        subprocess.run(venv_cmd)

        if args.upgrade:
            print("Upgrade pip to newest version")
            if system() == "Windows":
                time.sleep(3)   # wait to release handle of pip file
            subprocess.run(pip_cmd + ["--upgrade", "pip"])

        if options:
            print("Installing packages")
            subprocess.run(pip_cmd + options)

        print("Create environment succeed, activate the virtual environment by the following command:")
        print(activate_cmd)

    except Exception as e:
        print("Build failed")
        print(e)


config = {
    "cfg": {
        "name": "start",
        "help": "Start a project with virtual environment",
        "description": "Start a project with virtual environment. If not pass the project name, "
        "it will use the current directory name as the project name",
        "usage": "%(prog)s <project_name> [options]",
    },
    "arguments": [
        {
            "flags": ("project_name", ),
            "kwargs": {
                "nargs": "?",
                "default": os.path.basename(os.getcwd()),
                "help": "Name of new project, default is current folder"
            }
        },
        {
            "flags": ("-p", "--package"),
            "kwargs": {
                "action": "extend",
                "nargs": "*",
                "help": "Package which will be auto installed after created environment"
            }
        },
        {
            "flags": ("-r", "--requirement"),
            "kwargs": {
                "nargs": "?",
                "help": "Requirement file of packages to install"
            }
        },
        {
            "flags": ("-n", "--vname"),
            "kwargs": {
                "default": ".venv",
                "help": "Name of virtual environment dir, default to '.venv'"
            }
        },
        {
            "flags": ("-u", "--upgrade"),
            "kwargs": {
                "action": "store_true",
                "help": "Whether upgrade pip to newest"
            }
        },
        {
            "flags": ("-f", "--force"),
            "kwargs": {
                "action": "store_true",
                "help": "Whether overwrite existing environment"
            }
        },
        {
            "flags": ("--default",),
            "kwargs": {
                "default": [],
                "action": "extend",
                "nargs": "*",
                "help": "Save some package which will be auto install when a new virtual environment was be created."
            }
        },
        {
            "flags": ("--remove_default", ),
            "kwargs": {
                "action": "store_true",
                "help": "Remove saved packages which will be auto install."
            }
        }
    ],
    "func": start,
}
