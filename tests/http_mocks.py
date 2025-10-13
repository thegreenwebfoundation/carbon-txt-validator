"""
This module contains pytest fixtures which set up mocks for HTTP and DNS requests
needed when testing the carbon.txt finder: This allows us to make sure our tests
are decoupled from any real infrastructure, and that they can be run without an
internet connection. If you are writing a test which needs to exercise the carbon.txt
finder, you can rely on one of these fixtures, like so:

def test_finder(mocked_carbon_text_url):
    response = httpx.get(mocked_carbon_text_url)
    assert(response.status_code == 200)

The available mocks are as follows:
    - mocked_carbon_txt_url
        (url with path to carbon.txt, returns valid TOML with 200 response)
    - mocked_carbon_txt_domain
        (domain only, valid TOML, 200 response)
    - mocked_domain_with_www_fallback
        (domain only, with a valid carbon.txt on the www. subdomain of the TLD returned)
    - mocked_http_delegating_carbon_txt_url
        (url with path, delegates to other domain with HTTP header, other domain
        returns valid TOML with 200 response)
    - mocked_http_delegating_carbon_txt_domain
        (domain only, delegates to other domain with HTTP header, other domain
        returns valid TOML with 200 response)
    - mocked_dns_delegating_carbon_txt_url
        (url with path, redirects to other domain wtih DNS TXT record, other domain
        returns valid TOML with 200 response)
    - mocked_dns_delegating_carbon_txt_domain
        (domain only, redirects to other domain wtih DNS TXT record, other domain
        returns valid TOML with 200 response)
    - mocked_404_carbon_txt_url
        (url with path, No delegation, request for carbon.txt returns 404 status.)
    - mocked_404_carbon_txt_domain
        (domain only, No delegation, request for carbon.txt returns 404 status.)

Why do we provide these fixtures, instead of just setting up the mocks in the tests themselves?
Firstly, because, while it might appear a bit "magic", it makes the tests themselves smaller and
easier to follow, and avoids repetition of setup code for common test scenarios. Secondly, and
more importantly, however, it allows us to mock HTTP request when running the api tests with
pytest-django: the mocks must be set up *before* the test itself, or they won't be available
in the live_server that pytest-django provides.

"""

import pytest
import re
from unittest.mock import MagicMock


# These annotations ensure that httpx_mock does not mock any *other* HTTP requests:
# In particular this is important for API integration tests as we want to make requests
# from the API itself.
@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                )
            ),
        )
    ]
)
def mocked_carbon_txt_domain(minimal_carbon_txt_org, httpx_mock) -> str:
    """
    Return a valid carbon.txt with a 200 response, and provide
    the domain name only to the test
    """
    domain = "example.com"
    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            content=minimal_carbon_txt_org,
            status_code=200,
            is_reusable=True,
            is_optional=True,
        )
        # Add failing requests for subdomains too, in order to test subdomain resolution
        httpx_mock.add_response(
            method=method,
            url=re.compile(f"https:\\/\\/.+\\.{domain}"),
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=re.compile(f"https:\\/\\/.+\\.{domain}\\/carbon.txt"),
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=re.compile(f"https:\\/\\/.+\\.{domain}\\/.well-known\\/carbon.txt"),
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
    return domain


@pytest.fixture
def mocked_carbon_txt_url(mocked_carbon_txt_domain) -> str:
    """
    Return a valid carbon.txt with a 200 response, and provide
    the full URL to carbon.txt to the test
    """
    return f"https://{mocked_carbon_txt_domain}/carbon.txt"


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                )
            ),
        )
    ]
)
def mocked_domain_with_www_fallback(minimal_carbon_txt_org, httpx_mock) -> str:
    """
    Return a valid carbon.txt with a 200 response, and provide
    the domain name only to the test
    """
    domain = "example.com"
    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://www.{domain}/carbon.txt",
            content=minimal_carbon_txt_org,
            status_code=200,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/.well-known/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
    return domain


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                )
            ),
        )
    ]
)
def mocked_http_delegating_carbon_txt_domain(minimal_carbon_txt_org, httpx_mock) -> str:
    """
    Return a domain which delegates carbon.txt using an HTTP header,
    Ensure the delegated URL responds with a valid carbon.txt and a 200 response.
    """
    domain = "delegating.example.com"
    managed_service_url = "https://managed-service.example.com/carbon.txt"
    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            status_code=404,
            content="",
            headers={"CarbonTxt-Location": managed_service_url},
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            status_code=404,
            content="",
            headers={"CarbonTxt-Location": managed_service_url},
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/.well-known/carbon.txt",
            status_code=404,
            content="",
            headers={"CarbonTxt-Location": managed_service_url},
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=re.compile(f"https?://{domain}"),
            status_code=200,
            content="",
            headers={"CarbonTxt-Location": managed_service_url},
            is_reusable=True,
            is_optional=True,
        )
    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=managed_service_url,
            status_code=200,
            content=minimal_carbon_txt_org,
            is_reusable=True,
            is_optional=True,
        )
    return domain


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                )
            ),
        )
    ]
)
def mocked_http_delegating_carbon_txt_url(minimal_carbon_txt_org, httpx_mock) -> str:
    """
    Return a URL which delegates carbon.txt using an HTTP header,
    Ensure that the requested URL responds with a valid response despite delegation.
    """
    domain = "delegating.example.com"
    managed_service_url = "https://managed-service.example.com/carbon.txt"
    url = f"https://{domain}/carbon.txt"
    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=url,
            status_code=200,
            content=minimal_carbon_txt_org,
            headers={"CarbonTxt-Location": managed_service_url},
            is_reusable=True,
            is_optional=True,
        )
    return url


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                ),
            ),
        )
    ]
)
def mocked_dns_delegating_carbon_txt_domain(
    minimal_carbon_txt_org, mocker, httpx_mock
) -> str:
    """
    Return a domain which delegates carbon.txt using a DNS TXT record,
    Ensure the delegated URL responds with a valid carbon.txt and a 200 response.
    """
    domain = "delegating.example.com"
    managed_service_url = "https://managed-service.example.com/carbon.txt"
    record = MagicMock()
    record.to_text.return_value = f'"carbon-txt-location={managed_service_url}"'

    def dns_lookup_side_effect(requested_domain, record_type):
        if requested_domain == domain:
            return [record]
        else:
            return []

    mocker.patch("dns.resolver.resolve", side_effect=dns_lookup_side_effect)
    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/.well-known/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=managed_service_url,
            status_code=200,
            content=minimal_carbon_txt_org,
            is_reusable=True,
            is_optional=True,
        )
    return domain


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                ),
            ),
        )
    ]
)
def mocked_dns_delegating_carbon_txt_url(
    minimal_carbon_txt_org,
    mocker,
    httpx_mock,
) -> str:
    """
    Return a URL which delegates carbon.txt using a DNS TXT record,
    Ensure that the requested URL responds with a valid response despite delegation.
    """
    domain = "delegating.example.com"
    managed_service_url = "https://managed-service.example.com/carbon.txt"
    url = f"https://{domain}/carbon.txt"
    record = MagicMock()
    record.to_text.return_value = f'"carbon-txt-location={managed_service_url}"'

    def dns_lookup_side_effect(requested_domain, record_type):
        if requested_domain == domain:
            return [record]
        else:
            return []

    mocker.patch("dns.resolver.resolve", side_effect=dns_lookup_side_effect)

    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/.well-known/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=managed_service_url,
            status_code=200,
            content=minimal_carbon_txt_org,
            is_reusable=True,
            is_optional=True,
        )
    return url


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                ),
            ),
        )
    ]
)
def mocked_404_carbon_txt_domain(httpx_mock) -> str:
    """
    Return a 404 error on requests for carbon.txt. Provide the domain
    name to the test.
    """
    domain = "non-existent.example.com"
    url = f"https://{domain}/carbon.txt"
    well_known_url = f"https://{domain}/.well-known/carbon.txt"
    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=url,
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=well_known_url,
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
    return domain


@pytest.fixture
def mocked_404_carbon_txt_url(mocked_404_carbon_txt_domain) -> str:
    """
    Return a 404 error on requests for carbon.txt. Provide the full
    URL to the test.
    """
    return f"https://{mocked_404_carbon_txt_domain}/carbon.txt"


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                ),
            ),
        )
    ]
)
def mocked_carbon_txt_domain_with_file_and_dns_delegation(
    httpx_mock, mocker, minimal_carbon_txt_org
) -> str:
    """
    Return a response which delegates carbon.txt using a
    DNS record, but also serves its own carbon.txt.
    Provide the domain name to the test.
    """
    domain = "delegating.example.com"
    managed_service_url = "https://managed-service.example.com/carbon.txt"
    record = MagicMock()
    record.to_text.return_value = f'"carbon-txt-location={managed_service_url}"'

    def dns_lookup_side_effect(requested_domain, record_type):
        if requested_domain == domain:
            return [record]
        else:
            return []

    mocker.patch("dns.resolver.resolve", side_effect=dns_lookup_side_effect)

    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            status_code=200,
            content=minimal_carbon_txt_org,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/.well-known/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=managed_service_url,
            status_code=200,
            content=minimal_carbon_txt_org,
            is_reusable=True,
            is_optional=True,
        )
    return domain


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                ),
            ),
        )
    ]
)
def mocked_carbon_txt_domain_with_file_and_http_delegation(
    httpx_mock, mocker, minimal_carbon_txt_org
) -> str:
    """
    Return a response which delegates carbon.txt using a
    DNS record, but also serves its own carbon.txt.
    Provide the domain name to the test.
    """
    domain = "delegating.example.com"
    http_managed_service_url = (
        "https://http-managed-service.example.com/carbon.txt"
    )

    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            status_code=200,
            content=minimal_carbon_txt_org,
            headers={"CarbonTxt-Location": http_managed_service_url},
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/.well-known/carbon.txt",
            status_code=404,
            headers={"CarbonTxt-Location": http_managed_service_url},
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}",
            status_code=200,
            content="",
            headers={"CarbonTxt-Location": http_managed_service_url},
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=http_managed_service_url,
            status_code=200,
            content=minimal_carbon_txt_org,
            is_reusable=True,
            is_optional=True,
        )
    return domain


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                ),
            ),
        )
    ]
)
def mocked_carbon_txt_domain_with_recursive_delegation(
    httpx_mock, mocker, minimal_carbon_txt_org
) -> str:
    """
    Return a response which delegates carbon.txt using a
    DNS record, to another domain which in turn delegates to a third
    domain, using HTTP, which hosts its own carbon.txt
    Provide the 1st domain name to the test.
    """
    domain = "delegating.example.com"
    first_managed_service_domain = "first-managed-service.example.com"
    second_managed_service_domain = "second-managed-service.example.com"
    record = MagicMock()
    record.to_text.return_value = (
        f'"carbon-txt-location={first_managed_service_domain}"'
    )

    def dns_lookup_side_effect(requested_domain, record_type):
        if requested_domain == domain:
            return [record]
        else:
            return []

    mocker.patch("dns.resolver.resolve", side_effect=dns_lookup_side_effect)

    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/.well-known/carbon.txt",
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{first_managed_service_domain}",
            headers={"CarbonTxt-Location": second_managed_service_domain},
            status_code=200,
            content="",
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{first_managed_service_domain}/carbon.txt",
            headers={"CarbonTxt-Location": second_managed_service_domain},
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{first_managed_service_domain}/.well-known/carbon.txt",
            headers={"CarbonTxt-Location": second_managed_service_domain},
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
        httpx_mock.add_response(
            method=method,
            url=f"https://{second_managed_service_domain}/carbon.txt",
            status_code=200,
            content=minimal_carbon_txt_org,
            is_reusable=True,
            is_optional=True,
        )
    return domain


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                ),
            ),
        )
    ]
)
def mocked_404_page_at_carbon_txt_path(httpx_mock, valid_html_not_found_page) -> str:
    """
    Return a 404 error on requests for example.com/carbon.txt, but still provide a valid
    HTML page, mimicking the common case for a 404 page for websites.
    """
    domain = "example.com"
    url = f"https://{domain}/carbon.txt"

    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            content=valid_html_not_found_page,
            status_code=404,
            is_reusable=True,
            is_optional=True,
        )
    return url


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "example.com"
                ),
            ),
        )
    ]
)
def mocked_not_found_page_at_carbon_txt_path(
    httpx_mock, valid_html_not_found_page
) -> str:
    """
    Return a 'Not Found' page on requests for example.com/carbon.txt,
    but provide a 200 response, mimicing static sites that default to
    serving a fallback index page when a specific file is not found instead
    of an explicit 404 error.
    """
    domain = "example.com"
    url = f"https://{domain}/carbon.txt"

    for method in ["get", "head"]:
        httpx_mock.add_response(
            method=method,
            url=f"https://{domain}/carbon.txt",
            content=valid_html_not_found_page,
            status_code=200,
            is_reusable=True,
            is_optional=True,
        )
    return url
