import subprocess

def check_git_install() -> bool:
    ret = subprocess.run("git", shell=True, capture_output=True)
    if ret.stdout and not ret.stderr:
        return True
    return False

def create_setup_py(file_path: str):
    template = """\
from setuptools import setup

setup(
    name="{name}",
    version="0.0.1",
    author="{author}",
    author_email="{author_mail}",
)
"""
    author = subprocess.run(
        "git config user.name",
        shell=True,
        capture_output=True
        ).stdout.decode("utf-8").strip()
    author_email = subprocess.run(
        "git config user.email",
        shell=True,
        capture_output=True
        ).stdout.decode("utf-8").strip()
    with open(file_path, "w") as f:
        f.write(template.format(name="package", author=author, author_mail=author_email))

if __name__ == "__main__":
    create_setup_py("setup.py")