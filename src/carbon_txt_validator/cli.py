import os
import sys
from pathlib import Path

import rich
import typer
from django.core.management import execute_from_command_line

from . import finders, parsers_toml

app = typer.Typer()
validate_app = typer.Typer()
web_app = typer.Typer()
app.add_typer(validate_app, name="validate")


file_finder = finders.FileFinder()
parser = parsers_toml.CarbonTxtParser()


@validate_app.command("domain")
def validate_domain(domain: str):

    result = file_finder.resolve_domain(domain)

    if result:
        rich.print(f"Carbon.txt file found at {result}.")
    else:
        rich.print(f"No valid carbon.txt file found on {domain}.")
        return 1

    # fetch and parse file

    content = parser.get_carbon_txt_file(result)
    # rich.print(content)
    parsed_result = parser.parse_toml(content)
    rich.print(parsed_result)
    vaidation_results = parser.validate_as_carbon_txt(parsed_result)
    rich.print(vaidation_results)

    return 0


@validate_app.command("file")
def validate_file(
    file_path: str = typer.Argument(
        ..., help="Path to carbon.txt file or '-' to read from STDIN"
    )
):

    if file_path == "-":
        content = typer.get_text_stream("stdin").read()
    else:
        try:
            result = file_finder.resolve_uri(file_path)
        except FileNotFoundError as e:
            full_file_path = Path(file_path).absolute()
            rich.print(f"No valid carbon.txt file found at {full_file_path}.")
            return 1

        if result:
            rich.print(f"Carbon.txt file found at {result}.")
            content = parser.get_carbon_txt_file(result)
        else:
            rich.print(f"No valid carbon.txt file found at {file_path}.")
            return 1

    parsed_result = parser.parse_toml(content)
    vaidation_results = parser.validate_as_carbon_txt(parsed_result)
    rich.print("-------")
    rich.print(parsed_result)

    return parsed_result


def configure_django(debug=True):
    """Configure Django settings programmatically"""

    # Get the path to the web directory containing manage.py
    web_dir = Path(__file__).parent / "web"

    if not web_dir.exists():
        rich.print(
            "[red]Error: Could not find web directory containing Django app[/red]"
        )
        sys.exit(1)

    # Add the web directory to the Python path
    sys.path.insert(0, str(web_dir))

    # Set the Django settings module
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "carbon_txt_validator.web.config.settings.production"
    )

    # Import Django settings after path setup
    import django

    django.setup()


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
    debug: bool = typer.Option(True, help="Run in debug mode"),
    server: str = typer.Option(
        "django",
        help="Run in as django server or in production with the granian server",
    ),
):
    """Run the carbon.txt validator web server"""

    # Configure Django first
    configure_django(debug=debug)

    web_dir = Path(__file__).parent / "web"
    os.chdir(web_dir)

    if server == "granian":
        rich.print("Running in production mode with Granian server")
        rich.print("\n ----------------\n")
        # Run Granian instead of Django development server
        os.system(
            f"granian --interface wsgi carbon_txt_validator.web.config.wsgi:application"
        )
    else:
        # Run Django development server
        execute_from_command_line(["manage.py", "runserver", f"{host}:{port}"])


if __name__ == "__main__":
    app()
