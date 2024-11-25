import marimo

__generated_with = "0.9.23"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import httpx
    import rich

    return httpx, mo, rich


@app.cell
def __(mo):
    mo.md(
        """
        # Validator API Checking Notebook

        This notebooks exists for quickly checking the output of checking an URL against the carbon-text-validator API.

        It is intended to check results against both:

        1. a local running instance of a server, listening at [http://0.0.0.0:9000](http://0.0.0.0:9000)
        2. a remote server at [https://carbon-txt-api.greenweb.org](https://carbon-txt-api.greenweb.org)
        """
    )
    return


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        """
        ### Enter the URL below to check it

        As soon as you tab out of the text input, the value is submitted to the API.
        """
    )
    return


@app.cell(hide_code=True)
def __(mo):
    text = mo.ui.text(
        placeholder="Search...",
        label="Enter the URL to a carbon.txt file try validating it. Tab out to fire the request",
        full_width=True,
    )
    text
    return (text,)


@app.cell(hide_code=True)
def __(mo):
    mo.md(r"""### What is the local result?""")
    return


@app.cell
def __(local_res):
    local_res.json()
    return


@app.cell(hide_code=True)
def __(mo):
    mo.md("""### And the remote result?""")
    return


@app.cell(hide_code=True)
def __(remote_res):
    remote_res.json()
    return


@app.cell(hide_code=True)
def __(check_url, httpx, rich):
    import datetime

    _live_url = "https://carbon-txt-api.greenweb.org"
    _local_url = "http://localhost:9000"

    def check_url_against_api(check_url, api_url):
        _now = datetime.datetime.now()
        _data = {"url": check_url}
        rich.print(f"Time is: {_now}")
        api_path = "/api/validate/url/"
        return httpx.post(
            f"{api_url}{api_path}", json=_data, follow_redirects=True, timeout=None
        )

    rich.inspect(check_url)
    # rich.print(res)

    remote_res = check_url_against_api(check_url, _live_url)
    local_res = check_url_against_api(check_url, _local_url)
    return check_url_against_api, datetime, local_res, remote_res


@app.cell(hide_code=True)
def __(text):
    check_url = text.value
    return (check_url,)


if __name__ == "__main__":
    app.run()
