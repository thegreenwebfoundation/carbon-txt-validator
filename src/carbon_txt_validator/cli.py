import typer
import rich

from . import finders, parsers_toml

app = typer.Typer()
validate_app = typer.Typer()
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
        result = file_finder.resolve_uri(file_path)
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


if __name__ == "__main__":
    app()
