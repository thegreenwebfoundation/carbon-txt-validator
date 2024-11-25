import json
import logging
import os
import sys

import django
import pydantic_core
import rich
import typer
from django.core.management import execute_from_command_line

from . import exceptions, schemas, validators

logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)
validate_app = typer.Typer()
web_app = typer.Typer()
app.add_typer(
    validate_app,
    name="validate",
    help="Validate carbon.txt files, either online, or locally.",
)

err_console = rich.console.Console(stderr=True)
validator = validators.CarbonTxtValidator()


def _log_validation_results(success=True):
    if success:
        rich.print("✅ Carbon.txt file syntax is valid! \n")
    else:
        rich.print("❌ Sad times. Carbon.txt file syntax is invalid. \n")


def _log_validated_carbon_txt_object(
    validation_results: schemas.CarbonTxtFile | list[pydantic_core.ErrorDetails],
):
    rich.print("------- \n")
    rich.print(validation_results)


@validate_app.command("domain")
def validate_domain(domain: str):
    validation_results = validator.validate_domain(domain)
    carbon_txt_file = validation_results.result

    if carbon_txt_file := validation_results.result:
        for log in validation_results.logs:
            rich.print(log)
        _log_validation_results(success=True)
        _log_validated_carbon_txt_object(carbon_txt_file)
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
):
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
            raise typer.Exit(code=0)

        for log in validation_results.logs:
            rich.print(log)
        _log_validation_results(success=False)
        _log_validated_carbon_txt_object(validation_results.exceptions)
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
):
    """Configure Django settings programmatically"""
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

        if server == "granian":
            rich.print("Running with Granian server")
            rich.print("\n ----------------\n")
            # Run Granian instead of Django development server
            os.system(
                (
                    "granian --interface wsgi "
                    f"--host {host} --port {port} "
                    "carbon_txt.web.config.wsgi:application"
                )
            )
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


if __name__ == "__main__":
    app()
