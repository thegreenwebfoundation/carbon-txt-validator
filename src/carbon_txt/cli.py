import json

import os
import subprocess
import sys
from typing import Optional

import django
import environ
import pydantic_core
import rich
import structlog
import typer
from django.core.management import execute_from_command_line
from django.conf import settings

from . import exceptions, log_config, schemas, validators  # noqa

logger = structlog.get_logger()
logger.info("Hello, World from CLI")

app = typer.Typer(no_args_is_help=True)
validate_app = typer.Typer()
web_app = typer.Typer()
app.add_typer(
    validate_app,
    name="validate",
    help="Validate carbon.txt files, either online, or locally.",
)

err_console = rich.console.Console(stderr=True)


def create_validator(
    plugins_dir: Optional[str], active_plugins: Optional[list[str]]
) -> validators.CarbonTxtValidator:
    """
    Return a CarbonTxtValidator instance with the given `plugins_dir` and `active_plugins` values set
    from environment variables if not provided via the function arguments.
    """
    # we can't rely on values in the django settings module being set at this point.
    # We might also want to run multiple plugins. So, we need to parse a string
    # like "my_plugin,my_other_plugin" into a list two strings
    env = environ.Env(
        ACTIVE_CARBON_TXT_PLUGINS=(list, []),
        CARBON_TXT_PLUGINS_DIR=(str, None),
    )

    if not active_plugins:
        active_plugins = env("ACTIVE_CARBON_TXT_PLUGINS")

    if not plugins_dir:
        plugins_dir = env("CARBON_TXT_PLUGINS_DIR")

    validator = validators.CarbonTxtValidator(
        plugins_dir=plugins_dir, active_plugins=active_plugins
    )
    return validator


def _log_validation_results(success=True):
    if success:
        rich.print("\n✅ Carbon.txt file syntax is valid! \n")
    else:
        rich.print("❌ Sad times. Carbon.txt file syntax is invalid. \n")


def _log_validated_carbon_txt_object(
    validation_results: schemas.CarbonTxtFile | list[pydantic_core.ErrorDetails],
):
    rich.print("------- \n")
    rich.print(validation_results)


def _log_processed_documents(document_results):
    rich.print("------- \n")
    rich.print("Results of processing linked documents in the carbon.txt file: \n")
    rich.print(document_results)


@validate_app.command("domain")
def validate_domain(
    domain: str,
    plugins_dir: str = typer.Option(
        None, "--plugins-dir", help="path to optional plugin directory"
    ),
):
    validator = create_validator(plugins_dir=plugins_dir, active_plugins=None)
    validation_results = validator.validate_domain(domain)
    carbon_txt_file = validation_results.result

    if carbon_txt_file := validation_results.result:
        for log in validation_results.logs:
            rich.print(log)
        _log_validation_results(success=True)
        _log_validated_carbon_txt_object(carbon_txt_file)
        if validation_results.document_results:
            _log_processed_documents(validation_results.document_results)
        raise typer.Exit(code=0)

    for log in validation_results.logs:
        rich.print(log)
    _log_validation_results(success=False)
    _log_validated_carbon_txt_object(validation_results.exceptions)
    raise typer.Exit(code=1)


@validate_app.command("file")
def validate_file(
    file_path: str = typer.Argument(
        ..., help="Path to carbon.txt file or '-' to read from STDIN"
    ),
    plugins_dir: str = typer.Option(
        None, "--plugins-dir", help="path to optional plugin directory"
    ),
    django_settings: str = typer.Option(
        None, "--django-settings", "-ds", help="path to Django settings module"
    ),
):
    validator = create_validator(plugins_dir=plugins_dir, active_plugins=None)
    if file_path == "-":
        content = typer.get_text_stream("stdin").read()
        validation_results = validator.validate_contents(content)
    else:
        validation_results = validator.validate_url(file_path)

        if carbon_txt_file := validation_results.result:
            for log in validation_results.logs:
                rich.print(log)
            _log_validation_results(success=True)
            _log_validated_carbon_txt_object(carbon_txt_file)
            if validation_results.document_results:
                _log_processed_documents(validation_results.document_results)
            # from logging_tree import printout

            # printout()
            # breakpoint()
            raise typer.Exit(code=0)

        for log in validation_results.logs:
            rich.print(log)
        _log_validation_results(success=False)
        _log_validated_carbon_txt_object(validation_results.exceptions)
        # breakpoint()
        # from logging_tree import printout

        # printout()
        raise typer.Exit(code=1)


@app.command()
def schema():
    """
    Generate a JSON Schema representation of a carbon.txt file for validation
    """
    schema = schemas.CarbonTxtFile.model_json_schema()

    err_console.print("JSON Schema for a carbon.txt file: \n")

    if sys.stdout.isatty():
        rich.print(json.dumps(schema, indent=2))
    else:
        print(json.dumps(schema, indent=2))
    raise typer.Exit(code=0)


def configure_django(
    settings_module: str = "carbon_txt.web.config.settings.development",
    plugins_dir: Optional[str] = None,
):
    """Configure Django settings programmatically"""
    if plugins_dir is not None:
        os.environ.setdefault("CARBON_TXT_PLUGINS_DIR", plugins_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    django.setup()


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
    server: str = typer.Option(
        "django",
        help="Run in as django server or in production with the granian server",
    ),
    production: bool = typer.Option(False, help="Run in production mode"),
    django_settings: str = typer.Option(
        None, "--django-settings", "-ds", help="path to Django settings module"
    ),
    plugins_dir: str = typer.Option(
        None, "--plugins-dir", help="path to optional plugin directory"
    ),
    migrate: bool = typer.Option(
        False, help="Run database migrations before starting server"
    ),
):
    """Run the carbon.txt validator web server"""

    try:
        # override the prod / non prod switch if a custom settings module is provided
        if django_settings:
            # because we want to support importing a custtom settings file in the
            # same directory where we are calling `carbon-txt serve` we add the current
            # directory to the python path
            sys.path.insert(0, os.getcwd())
            rich.print(f"Using custom settings module: {django_settings}")
            settings_module = django_settings
        else:
            if production:
                rich.print("Running in production mode")
                settings_module = "carbon_txt.web.config.settings.production"
            else:
                settings_module = "carbon_txt.web.config.settings.development"

        rich.print("\n ----------------\n")
        configure_django(
            settings_module=settings_module,
        )

        if migrate:
            execute_from_command_line(["manage.py", "migrate"])
        else:
            try:
                execute_from_command_line(["manage.py", "migrate", "--check"])
            except SystemExit as e:
                rich.print(
                    "[bold red]There are database migrations pending that must be applied before running the server![/bold red]"
                )
                rich.print(
                    "Please check your database settings are correct and re-run with the [bold]--migrate[/bold] flag."
                )
                rich.print(
                    f"Your current [bold]DATABASE_URL[/bold] is: [cyan bold]{settings.DATABASE_URL}[/cyan bold]."
                )
                raise e

        if server == "granian":
            rich.print("Running with Granian server")

            rich.print("\n ----------------\n")
            # Run Granian instead of Django development server

            cmd_args = [
                "granian",
                "--interface",
                "wsgi",
                "--host",
                str(host),
                "--port",
                str(port),
                # without the access log flag we see no requests in the logs
                "--access-log",
                "carbon_txt.web.config.wsgi:application",
            ]
            subprocess.run(cmd_args)
        else:
            execute_from_command_line(["manage.py", "runserver", f"{host}:{port}"])
    except exceptions.InsecureKeyException as e:
        rich.print(f"{e}")
        rich.print(
            "For more, see the docs at https://carbon-txt-validator.readthedocs.io/en/latest/deployment.html"
        )
        typer.Exit(code=1)
    # anything unexpected we provide a clear path to raising an issue to fix it
    except Exception as e:
        rich.print(f"An error occurred: {e}")
        rich.print(
            (
                "Please consider raising an issue at: "
                "https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/new, "
                "with steps to reproduce this error"
            )
        )
        raise typer.Exit(code=1)


@app.command()
def plugins(
    plugins_dir: str = typer.Option(
        None, "--plugins-dir", help="path to optional plugin directory"
    ),
):
    """List active plugins"""
    validator = create_validator(plugins_dir=plugins_dir, active_plugins=None)
    plugins = validator.list_plugins()

    if not plugins:
        err_console.print("No plugins are active.\n")
        err_console.print("See the docs to learn to activate plugins:\n")
        err_console.print(
            "https://carbon-txt-validator.readthedocs.io/en/latest/plugins.html"
        )
        raise typer.Exit(code=0)

    err_console.print("Active plugins: \n")

    for plugin in plugins:
        err_console.print(f" - {plugin.plugin_name}")

    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
