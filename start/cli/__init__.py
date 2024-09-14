import os

from typer import Typer

from start.cli.environment import activate, create, list_environments
from start.cli.inspect import list_packages, show
from start.cli.modify import add, remove
from start.cli.project import init, install, new

app = Typer(
    help="Package manager based on pip and venv",
    rich_markup_mode="markdown",
    pretty_exceptions_show_locals=bool(os.getenv("DEBUG")),
)

with_extra_args = {"allow_extra_args": True, "ignore_unknown_options": True}
app.command(rich_help_panel="Project", context_settings=with_extra_args)(new)
app.command(rich_help_panel="Project", context_settings=with_extra_args)(init)
app.command(rich_help_panel="Project", context_settings=with_extra_args)(install)

app.command(rich_help_panel="Modify Dependencies", context_settings=with_extra_args)(add)
app.command(rich_help_panel="Modify Dependencies", context_settings=with_extra_args)(remove)

app.command(name="list", rich_help_panel="Inspect")(list_packages)
app.command(rich_help_panel="Inspect")(show)

env_typer = Typer(help="Manager environments.")

env_typer.command(context_settings=with_extra_args)(create)
env_typer.command()(activate)
env_typer.command(name="list")(list_environments)

app.add_typer(env_typer, name="env", rich_help_panel="Environment")
