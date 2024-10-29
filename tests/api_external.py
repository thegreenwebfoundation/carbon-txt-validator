import httpx
import rich

from rich import pretty

with open("./tests/fixtures/aremythirdpartiesgreen.com.carbon-txt.toml") as toml_file:
    toml_contents = toml_file.read()

    api_url = "http://127.0.0.1:8000/api/validate/"
    data = {"domain": "string", "text_contents": toml_contents}
    res = httpx.post(api_url, json=data, follow_redirects=True)
    rich.print(res)
    pretty.pprint(res.json())
