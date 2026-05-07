import json

import httpx


def test_all_requests_allowed_when_auth_not_required(
    mocker, live_server, mocked_carbon_txt_url
):
    """
    When API key auth is switched off, all requests are allowed.
    """

    # GIVEN API key auth is switched off
    mock_settings = mocker.patch("carbon_txt.web.api_key_auth.settings")
    mock_settings.REQUIRE_API_KEY = False

    # WHEN I make a request without an API key
    api_url = f"{live_server.url}/api/validate/url"
    data = {"url": mocked_carbon_txt_url}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    # THEN I get a succesful response
    assert res.status_code == 200


def test_unauthorized_request_not_allowed_when_auth_required(
    mocker, live_server, mocked_carbon_txt_url
):
    """
    When API key auth is switched on, unauthorized requests are not allowed.
    """

    # GIVEN API key auth is switched on
    mock_settings = mocker.patch("carbon_txt.web.api_key_auth.settings")
    mock_settings.REQUIRE_API_KEY = True

    # WHEN I make an unauthorized request
    api_url = f"{live_server.url}/api/validate/url"
    data = {"url": mocked_carbon_txt_url}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    # THEN I receive an unauthorized response
    assert res.status_code == 401


def test_authorized_request_with_valid_key_in_query_string_allowed_when_auth_required(
    mocker, httpx_mock, live_server, mocked_carbon_txt_url
):
    """
    When API key auth is switched on, authorized requests
    with a valid API key in the query string are allowed.
    """

    # GIVEN API key auth is switched on
    mock_settings = mocker.patch("carbon_txt.web.api_key_auth.settings")
    mock_settings.REQUIRE_API_KEY = True
    mock_settings.API_KEY_INTROSPECTION_URL = "http://example.com/introspect"
    mock_settings.GWF_SHARED_SECRET = "def456"

    httpx_mock.add_response(
        url=mock_settings.API_KEY_INTROSPECTION_URL, json={"active": True}
    )

    # WHEN I make a request with an authorized token in the query string
    api_key = "abc123"
    api_url = f"{live_server.url}/api/validate/url?api_key={api_key}"
    data = {"url": mocked_carbon_txt_url}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)

    # THEN I get a succesful response
    assert res.status_code == 200

    # AND the introspection API is called correctly
    assert request.headers["X-GWF-Shared-Secret"] == mock_settings.GWF_SHARED_SECRET
    assert body["token"] == api_key


def test_authorized_request_with_valid_key_in_header_allowed_when_auth_required(
    mocker, httpx_mock, live_server, mocked_carbon_txt_url
):
    """
    When API key auth is switched on, authorized requests
    with a valid API key in the request headers are allowed.
    """

    # GIVEN API key auth is switched on
    mock_settings = mocker.patch("carbon_txt.web.api_key_auth.settings")
    mock_settings.REQUIRE_API_KEY = True
    mock_settings.API_KEY_INTROSPECTION_URL = "http://example.com/introspect"
    mock_settings.GWF_SHARED_SECRET = "def456"

    httpx_mock.add_response(
        url=mock_settings.API_KEY_INTROSPECTION_URL, json={"active": True}
    )

    # WHEN I make a request with an authorized token in the request headers
    api_key = "abc123"
    api_url = f"{live_server.url}/api/validate/url"
    data = {"url": mocked_carbon_txt_url}
    headers = {"X-Api-Key": api_key}
    res = httpx.post(
        api_url, json=data, headers=headers, follow_redirects=True, timeout=None
    )

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)

    # THEN I get a succesful response
    assert res.status_code == 200

    # AND the introspection API is called correctly
    assert request.headers["X-GWF-Shared-Secret"] == mock_settings.GWF_SHARED_SECRET
    assert body["token"] == api_key


def test_authorized_request_with_invalid_key_in_query_string_not_allowed_when_auth_required(
    mocker, httpx_mock, live_server, mocked_carbon_txt_url
):
    """
    When API key auth is switched on, authorized requests
    with an invalid API key in the query string are not allowed.
    """

    # GIVEN API key auth is switched on
    mock_settings = mocker.patch("carbon_txt.web.api_key_auth.settings")
    mock_settings.REQUIRE_API_KEY = True
    mock_settings.API_KEY_INTROSPECTION_URL = "http://example.com/introspect"
    mock_settings.GWF_SHARED_SECRET = "def456"

    httpx_mock.add_response(
        url=mock_settings.API_KEY_INTROSPECTION_URL, json={"active": False}
    )

    # When I make a request with an unauthorized token in the query string
    api_key = "abc123"
    api_url = f"{live_server.url}/api/validate/url?api_key={api_key}"
    data = {"url": mocked_carbon_txt_url}
    res = httpx.post(api_url, json=data, follow_redirects=True, timeout=None)

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)

    # THEN I receive un unauthorized response
    assert res.status_code == 401

    # AND the introspection API is called correctly
    assert request.headers["X-GWF-Shared-Secret"] == mock_settings.GWF_SHARED_SECRET
    assert body["token"] == api_key


def test_authorized_request_with_invalid_key_in_header_not_allowed_when_auth_required(
    mocker, httpx_mock, live_server, mocked_carbon_txt_url
):
    """
    When API key auth is switched on, authorized requests
    with an invalid API key in the request headers are not allowed.
    """

    # GIVEN API key auth is switched on
    mock_settings = mocker.patch("carbon_txt.web.api_key_auth.settings")
    mock_settings.REQUIRE_API_KEY = True
    mock_settings.API_KEY_INTROSPECTION_URL = "http://example.com/introspect"
    mock_settings.GWF_SHARED_SECRET = "def456"

    httpx_mock.add_response(
        url=mock_settings.API_KEY_INTROSPECTION_URL, json={"active": False}
    )

    # When I make a request with an unauthorized token in the request headers
    api_key = "abc123"
    api_url = f"{live_server.url}/api/validate/url"
    data = {"url": mocked_carbon_txt_url}
    headers = {"X-Api-Key": api_key}
    res = httpx.post(
        api_url, json=data, headers=headers, follow_redirects=True, timeout=None
    )

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)

    # THEN I receive un unauthorized response
    assert res.status_code == 401

    # AND the introspection API is called correctly
    assert request.headers["X-GWF-Shared-Secret"] == mock_settings.GWF_SHARED_SECRET
    assert body["token"] == api_key
