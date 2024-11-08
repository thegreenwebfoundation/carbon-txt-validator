from pathlib import Path

import httpx
import pytest


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_endpoint_ok(
    live_server, shorter_carbon_txt_string, url_suffix
):
    api_url = f"{live_server.url}/api/validate/file{url_suffix}"
    data = {"text_contents": shorter_carbon_txt_string}
    res = httpx.post(api_url, json=data, follow_redirects=True)

    assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_endpoint_fail(live_server, url_suffix):
    path_to_failing_file = (
        Path() / "tests" / "fixtures" / "aremythirdpartiesgreen.com.carbon-txt.toml"
    )

    with open(path_to_failing_file) as toml_file:
        api_url = f"{live_server.url}/api/validate/file{url_suffix}"
        data = {"text_contents": toml_file.read()}
        res = httpx.post(api_url, json=data, follow_redirects=True)

        assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_url_endpoint_ok(live_server, url_suffix):
    api_url = f"{live_server.url}/api/validate/url{url_suffix}"
    data = {"url": "https://aremythirdpartiesgreen.com/carbon.txt"}
    res = httpx.post(api_url, json=data, follow_redirects=True)

    assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_url_endpoint_fail(live_server, url_suffix):
    api_url = f"{live_server.url}/api/validate/url{url_suffix}"
    data = {"url": "https://aremythirdpartiesgreen.com/carbon.txt"}
    res = httpx.post(api_url, json=data, follow_redirects=True)

    assert res.status_code == 200


# TODO do we still need to run this with a full on external server?
def test_hitting_fetch_json_schema(live_server):
    api_url = f"{live_server.url}/api/json_schema"
    res = httpx.get(api_url, follow_redirects=True)
    assert res.status_code == 200
