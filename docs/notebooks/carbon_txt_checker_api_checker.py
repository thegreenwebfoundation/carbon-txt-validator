import marimo

__generated_with = "0.9.23"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import httpx
    import rich

    return httpx, mo, rich


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        """
        # Validator API Checking Notebook

        This notebooks exists for quickly checking the output of checking an URL against the carbon-text-validator API.

        It is intended to check results against a default remote server at [https://carbon-txt-api.greenweb.org](https://carbon-txt-api.greenweb.org), but allows you to override the server that you send requests to.

        This is useful for local testing, if you are running a local server on port 9000, you would update it to be [http://localhost:9000](http://localhost:9000).
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
    api_server = mo.ui.text(
        value="https://carbon-txt-api.greenweb.org",
        placeholder="Search...",
        label="Enter the URL of the server you are sending an API request to, if you're not using the default server",
        full_width=True,
    )
    api_server
    return (api_server,)


@app.cell(hide_code=True)
def __(mo):
    mo.md(r"""### API Response""")
    return


@app.cell
def __(res):
    res.content
    return


@app.cell(hide_code=True)
def __(api_server, check_url, httpx, rich):
    import datetime

    def check_url_against_api(check_url, api_url):
        _now = datetime.datetime.now()
        _data = {"url": check_url}
        rich.print(f"Time is: {_now}")
        api_path = "/api/validate/url/"
        return httpx.post(
            f"{api_url}{api_path}", json=_data, follow_redirects=True, timeout=None
        )

    # rich.inspect(check_url)
    if api_server.value:
        res = check_url_against_api(check_url, api_server.value)
    return check_url_against_api, datetime, res


@app.cell(hide_code=True)
def __(text):
    check_url = text.value
    return (check_url,)


@app.cell
def __(res):
    res
    return


@app.cell
def __(res):
    res.status_code
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
