import typer
import httpx
import dns.resolver
import tomllib as toml
import rich

app = typer.Typer()
validate_app = typer.Typer()
app.add_typer(validate_app, name="validate")


@validate_app.command("domain")
def validate_domain(domain: str):


    dns_record = dns.resolver.resolve(domain, "TXT")
    url = dns_record[0].strings[0].decode()

    httpx.get(url)
        content = response.text
    data = toml.loads(content)
    rich.print(data)
    # Process the data...


@validate_app.command("url")
def validate_url(url: str):
    breakpoint()
    with httpx.Client() as client:
        response = client.get(url)
        content = response.text
    data = toml.loads(content)
    rich.print(data)
    # Process the data...


@validate_app.command("file")
def validate_file(file_path: str):
    with open(file_path, "r") as file:
        content = file.read()
    data = toml.loads(content)
    rich.print(data)
    # Process the data...


@validate_app.command("stdin")
def validate_stdin():
    content = typer.get_text_stream("stdin").read()
    data = toml.loads(content)
    rich.print(data)
    # Process the data...


if __name__ == "__main__":
    app()
