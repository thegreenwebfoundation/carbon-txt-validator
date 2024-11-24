from pathlib import Path

import httpx
import pytest
import logging

logger = logging.getLogger(__name__)


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


def test_hitting_validate_url_endpoint_with_via_delegation(live_server):
    """
    When we have a carbon.txt url that is delegating to a another server
    using the http 'via' header, does it follow the delegation and return the
    correct response?
    """
    api_url = f"{live_server.url}/api/validate/url/"
    data = {"url": "https://hosted.carbontxt.org/carbon.txt"}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    assert res.status_code == 200
    actual_provider_domain = res.json()["data"]["org"]["credentials"][0]["domain"]
    assert actual_provider_domain == "managed-service.carbontxt.org"


def test_hitting_validate_url_endpoint_with_txt_delegation(live_server):
    """
    When we have a carbon.txt url that is delegating to a another server
    using the DNS txt record, does it follow the delegation and return the
    correct response?
    """
    api_url = f"{live_server.url}/api/validate/url/"
    data = {"url": "https://delegating-with-txt-record.carbontxt.org/carbon.txt"}
    res = httpx.post(api_url, json=data, follow_redirects=True)
    assert res.status_code == 200

    # https://used-in-tests.carbontxt.org/carbon.txt

    # TODO: Should we serve a different error here, like a 40x?
    # actual_provider_domain = res.json()["data"]["org"]["credentials"][0]["domain"]
    # assert actual_provider_domain == "managed-service.carbontxt.org"


# TODO: Do we still need to run this with a full on external server?
# This is captured in #32 - You need a router class to run the tests without
# the live server
# https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/32
def test_hitting_fetch_json_schema(live_server):
    api_url = f"{live_server.url}/api/json_schema"
    res = httpx.get(api_url, follow_redirects=True)
    assert res.status_code == 200
