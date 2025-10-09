from pathlib import Path

import httpx
import pytest

from structlog import get_logger

logger = get_logger()


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_endpoint_ok(
    live_server, shorter_carbon_txt_string, url_suffix
):
    api_url = f"{live_server.url}/api/validate/file{url_suffix}"
    data = {"text_contents": shorter_carbon_txt_string}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_endpoint_fail(live_server, url_suffix):
    path_to_failing_file = (
        Path() / "tests" / "fixtures" / "aremythirdpartiesgreen.com.carbon-txt.toml"
    )

    with open(path_to_failing_file) as toml_file:
        api_url = f"{live_server.url}/api/validate/file{url_suffix}"
        data = {"text_contents": toml_file.read()}
        res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

        assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_url_endpoint_ok(
    live_server, url_suffix, mocked_carbon_txt_url
):
    api_url = f"{live_server.url}/api/validate/url{url_suffix}"
    data = {"url": mocked_carbon_txt_url}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_url_endpoint_fail(
    live_server, url_suffix, mocked_404_carbon_txt_url
):
    api_url = f"{live_server.url}/api/validate/url{url_suffix}"
    data = {"url": mocked_404_carbon_txt_url}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_url_endpoint_with_http_header_delegation(
    live_server, url_suffix, mocked_http_delegating_carbon_txt_url
):
    """
    When we have a carbon.txt URL that is delegating to a another server
    using the HTTP 'CarbonTxt-Location' header, does it follow the delegation and return the
    correct response?
    """
    api_url = f"{live_server.url}/api/validate/url{url_suffix}"
    data = {"url": mocked_http_delegating_carbon_txt_url}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    assert res.status_code == 200
    actual_provider_domain = res.json()["data"]["org"]["disclosures"][0]["domain"]
    assert actual_provider_domain == "used-in-tests.carbontxt.org"


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_url_endpoint_with_txt_delegation(
    live_server, url_suffix, mocked_dns_delegating_carbon_txt_url
):
    """
    When we have a carbon.txt URL that is delegating to a another server
    using the DNS TXT record, does it follow the delegation and return the
    correct response?
    """
    api_url = f"{live_server.url}/api/validate/url{url_suffix}"
    data = {"url": mocked_dns_delegating_carbon_txt_url}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)
    assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_domain_endpoint_ok(
    live_server, url_suffix, mocked_carbon_txt_domain
):
    api_url = f"{live_server.url}/api/validate/domain{url_suffix}"
    data = {"domain": mocked_carbon_txt_domain}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)
    actual_url = res.json()["url"]
    delegation_method = res.json()["delegation_method"]

    assert res.status_code == 200
    assert actual_url == f"https://{mocked_carbon_txt_domain}/carbon.txt"
    assert delegation_method is None


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_domain_endpoint_fail(
    live_server, url_suffix, mocked_404_carbon_txt_domain
):
    api_url = f"{live_server.url}/api/validate/domain{url_suffix}"
    data = {"domain": mocked_404_carbon_txt_domain}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    assert res.status_code == 200


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_domain_endpoint_with_http_header_delegation(
    live_server, url_suffix, mocked_http_delegating_carbon_txt_domain
):
    """
    When we have a carbon.txt URL that is delegating to a another server
    using the HTTP 'CarbonTxt-Location' header, does it follow the delegation and return the
    correct response?
    """
    api_url = f"{live_server.url}/api/validate/domain{url_suffix}"
    data = {"domain": mocked_http_delegating_carbon_txt_domain}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)
    actual_url = res.json()["url"]
    delegation_method = res.json()["delegation_method"]

    assert res.status_code == 200
    assert actual_url == "https://managed-service.example.com/carbon.txt"
    assert delegation_method == "http"


@pytest.mark.parametrize("url_suffix", ["", "/"])
def test_hitting_validate_domain_endpoint_with_txt_delegation(
    live_server, url_suffix, mocked_dns_delegating_carbon_txt_domain
):
    """
    When we have a carbon.txt URL that is delegating to a another server
    using the DNS TXT record, does it follow the delegation and return the
    correct response?
    """
    api_url = f"{live_server.url}/api/validate/domain{url_suffix}"
    data = {"domain": mocked_dns_delegating_carbon_txt_domain}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)
    actual_url = res.json()["url"]
    delegation_method = res.json()["delegation_method"]

    assert res.status_code == 200
    assert actual_url == "https://managed-service.example.com/carbon.txt"
    assert delegation_method == "dns"


# TODO: Do we still need to run this with a full on external server?
# This is captured in #32 - You need a router class to run the tests without
# the live server
# https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/32
def test_hitting_fetch_json_schema(live_server):
    api_url = f"{live_server.url}/api/json_schema"
    res = httpx.get(api_url, follow_redirects=True, timeout=None)
    assert res.status_code == 200


def test_hitting_validate_with_plugins_dir_set(
    # we need the transactional_db fixture because without it the
    # live_server from the previous tests is used, and
    # they do not have a `plugins_dir` active
    settings_with_plugin_dir_set,
    transactional_db,
    live_server,
    shorter_carbon_txt_string,
):
    api_url = f"{live_server.url}/api/validate/file"
    data = {"text_contents": shorter_carbon_txt_string}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)
    assert res.status_code == 200

    parsed_response = res.json()
    parsed_response

    # do we have the output from the Test Plugin in the logs?
    assert res.status_code == 200
    assert any("Test Plugin" in log for log in parsed_response["logs"])

    # do we see the return values of the hook function in document results?
    plugin_data = parsed_response.get("document_data").get("test_plugin")
    assert plugin_data is not None
    assert plugin_data[0]["test_key"] == "TEST PLUGIN VALUE"


def test_hitting_validate_with_plugins_raising_errors(
    # we need the transactional_db fixture because without it the
    # live_server from the previous tests is used, and
    # they do not have a `plugins_dir` active
    settings_with_active_csrd_greenweb_plugin,
    transactional_db,
    live_server,
):
    """ """
    api_url = f"{live_server.url}/api/validate/url"
    data = {
        "url": "https://used-in-tests.carbontxt.org/carbon-txt-with-csrd-no-renewables-data.txt"
    }
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)
    assert res.status_code == 200

    parsed_response = res.json()
    parsed_response

    # do we have the output from the csrd plugin? in the logs?
    assert res.status_code == 200

    # csrd_greenweb is the plugin we active for this data
    assert "csrd_greenweb" in parsed_response.get("document_data").keys()

    # do we see the return values of the hook function in document results?
    plugin_data = parsed_response.get("document_data").get("csrd_greenweb")

    assert plugin_data is not None

    # we should see an error key in every item in the plugin data
    for item in plugin_data:
        assert "error" in item.keys()
        assert "datapoint_short_code" in item.keys()
        assert "datapoint_readable_label" in item.keys()
        assert item["error"] == "NoMatchingDatapointsError"

    # check that we see the correct datapoint short code and human friendly value
    # in at least one of the error messages
    assert any(
        item.get("datapoint_short_code")
        == "PercentageOfRenewableSourcesInTotalEnergyConsumption"
        for item in plugin_data
    )


def test_hitting_validate_with_zero_plugins_set(
    transactional_db,
    live_server,
    shorter_carbon_txt_string,
):
    """
    Even when no plugins are set, we should still send an empty
    dictionary / object over the API.
    """
    api_url = f"{live_server.url}/api/validate/file"
    data = {"text_contents": shorter_carbon_txt_string}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)
    assert res.status_code == 200
    parsed_response = res.json()
    assert "document_data" in parsed_response.keys()
    assert parsed_response["document_data"] == {}
