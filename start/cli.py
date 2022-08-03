from email.policy import default
import click

import os

@click.group()
def cli():
    """Pip0 is a package and virtual environment manager for Python. Based on pip."""


@cli.command()
def install():
    """Install packages, compatibility with 'pip install'"""

@cli.command()
@click.argument('name', nargs=1, default=os.path.basename(os.getcwd()))
@click.option("-p", "--package", multiple=True, metavar="",
              help="Package which will be auto installed after created environment")
@click.option("-r", "--requirement", metavar="",
              help="Requirement file of packages to install")
@click.option("-n", "--vname", default=".venv", metavar="",
              help="Name of virtual environment dir, default to '.venv'")
@click.option("-u", "--upgrade", is_flag=True,
              help="Whether upgrade pip to newest")
@click.option("-f", "--force", is_flag=True,
              help="Whether overwrite existing environment")
@click.option("-d", "--default", multiple=True, metavar="",
              help="Save some package which will be auto install when a new virtual environment was be created.")
@click.option("--remove_default", is_flag=True,
              help="Remove saved packages which will be auto install.")
def start(name, **kwargs):
    """
    Start a project with virtual environment. If not pass the project name,
    it will use the current directory name as the project name.
    """
    click.echo(name)
    click.echo(kwargs)




if __name__ == '__main__':
    cli()