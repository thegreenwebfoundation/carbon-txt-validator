import json
import logging
import os
import sys
from pathlib import Path

import django
import rich
import typer
from django.core.management import execute_from_command_line

from . import finders, parsers_toml
from . import exceptions
from .schemas import CarbonTxtFile

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


file_finder = finders.FileFinder()
parser = parsers_toml.CarbonTxtParser()


def _log_validation_results(success=True):
    if success:
        rich.print("✅ Carbon.txt file syntax is valid! \n")
    else:
        rich.print("❌ Sad times. Carbon.txt file syntax is invalid. \n")


def _log_validated_carbon_txt_object(validation_results: CarbonTxtFile = None):
    rich.print("------- \n")
    rich.print(validation_results)


@validate_app.command("domain")
def validate_domain(domain: str):
    result = file_finder.resolve_domain(domain)

    if result:
        rich.print(f"Carbon.txt file found at {result}.\n")
    else:
        rich.print(f"No valid carbon.txt file found on {domain}.\n")
        typer.Exit(code=1)

    # fetch and parse file
    content = parser.get_carbon_txt_file(result)
    parsed_result = parser.parse_toml(content)
    validation_results = parser.validate_as_carbon_txt(parsed_result)

    # log the results
    if isinstance(validation_results, CarbonTxtFile):
        _log_validation_results(success=True)
        _log_validated_carbon_txt_object(validation_results)
        typer.Exit(code=0)
    else:
        _log_validation_results(success=False)
        _log_validated_carbon_txt_object(validation_results)
        typer.Exit(code=1)


@validate_app.command("file")
def validate_file(
    file_path: str = typer.Argument(
        ..., help="Path to carbon.txt file or '-' to read from STDIN"
    ),
):
    if file_path == "-":
        content = typer.get_text_stream("stdin").read()
        parsed_result = parser.parse_toml(content)
    else:
        try:
            result = file_finder.resolve_uri(file_path)
            parsed_result = parser.fetch_parsed_carbon_txt_file(result)

        # the file path is local, but we can't access it
        except FileNotFoundError:
            full_file_path = Path(file_path).absolute()
            rich.print(f"No valid carbon.txt file found at {full_file_path}. \n")
            raise typer.Exit(code=1)

        # the file path is remote, and we can't access it
        except exceptions.UnreachableCarbonTxtFile as e:
            logger.error(f"Error: {e}")
            raise typer.Exit(code=1)

        # the file path is reachable, and but it's not valid TOML
        except exceptions.NotParseableTOML as e:
            rich.print(
                f"A carbon.txt file was found at {file_path}: but it wasn't parseable TOML. Error was: {e}"
            )
            raise typer.Exit(code=1)

        except Exception as e:
            rich.print(f"An unexpected error occurred: {e}")
            raise typer.Exit(code=1)

    validation_results = parser.validate_as_carbon_txt(parsed_result)

    if isinstance(validation_results, CarbonTxtFile):
        _log_validation_results(success=True)
        _log_validated_carbon_txt_object(validation_results)
        return typer.Exit(code=0)
    else:
        _log_validation_results(success=False)
        _log_validated_carbon_txt_object(validation_results)
        return typer.Exit(code=0)


@app.command()
def schema():
    """
    Generate a JSON Schema representation of a carbon.txt file for validation
    """
    schema = CarbonTxtFile.model_json_schema()

    err_console.print("JSON Schema for a carbon.txt file: \n")

    if sys.stdout.isatty():
        rich.print(json.dumps(schema, indent=2))
    else:
        print(json.dumps(schema, indent=2))
    typer.Exit(code=0)


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
        typer.Exit(code=1)


if __name__ == "__main__":
    app()
