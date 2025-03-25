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
    - mocked_http_delegating_carbon_txt_url
        (url with path, delegates to other domain with Via header, other domain
        returns valid TOML with 200 resposne)
    - mocked_http_delegating_carbon_txt_domain
        (domain only, delegates to other domain with Via header, other domain
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


# These annotations ensure that httpx_mock does not mock any *other* http requests:
# In particular this is important for API integration tests as we want to make requests
# from the API itself.
@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "withcarbontxt.example.com"
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
    domain = "withcarbontxt.example.com"
    httpx_mock.add_response(
        url=f"https://{domain}/carbon.txt",
        content=minimal_carbon_txt_org,
        status_code=200,
        is_reusable=True,
        is_optional=True,
    )
    return domain


@pytest.fixture
def mocked_carbon_txt_url(mocked_carbon_txt_domain) -> str:
    """
    Return a valid carbon.txt with a 200 response, and provide
    the full url to carbon.txt to the test
    """
    return f"https://{mocked_carbon_txt_domain}/carbon.txt"


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "withcarbontxt.example.com"
                )
            ),
        )
    ]
)
def mocked_http_delegating_carbon_txt_domain(minimal_carbon_txt_org, httpx_mock) -> str:
    """
    Return a domain which delegates carbon.txt using an HTTP via header,
    Ensure the delegated URL responds with a valid carbon.txt and a 200 response.
    """
    domain = "delegating.withcarbontxt.example.com"
    managed_service_url = "https://delegate.withcarbontxt.example.com/carbon.txt"
    domain_hash_check = "deadb33fdeadf00d"  # TODO: This will need to be generated properly once verification is in place
    httpx_mock.add_response(
        url=re.compile(f"https?://{domain}"),
        status_code=204,
        content="",
        headers={"Via": f"1.1 {managed_service_url} {domain_hash_check}"},
        is_reusable=True,
    )
    httpx_mock.add_response(
        url=managed_service_url,
        status_code=200,
        content=minimal_carbon_txt_org,
        is_reusable=True,
    )
    return domain


@pytest.fixture
def mocked_http_delegating_carbon_txt_url(
    mocked_http_delegating_carbon_txt_domain,
) -> str:
    """
    Return a URL which delegates carbon.txt using an HTTP via header,
    Ensure the delegated URL responds with a valid carbon.txt and a 200 response.
    """
    return f"https://{mocked_http_delegating_carbon_txt_domain}/carbon.txt"


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "withcarbontxt.example.com"
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
    domain = "delegating.withcarbontxt.example.com"
    managed_service_url = "https://delegate.withcarbontxt.example.com/carbon.txt"
    domain_hash_check = "deadb33fdeadf00d"  # TODO: This will need to be generated properly once verification is in place
    record = MagicMock()
    record.to_text.return_value = (
        f'"carbon-txt={managed_service_url} {domain_hash_check}"'
    )

    def dns_lookup_side_effect(requested_domain, record_type):
        if requested_domain == domain:
            return [record]
        else:
            return []

    mocker.patch("dns.resolver.resolve", side_effect=dns_lookup_side_effect)
    httpx_mock.add_response(
        url=managed_service_url,
        status_code=200,
        content=minimal_carbon_txt_org,
        is_reusable=True,
        is_optional=True,
    )
    return domain


@pytest.fixture
def mocked_dns_delegating_carbon_txt_url(
    mocked_dns_delegating_carbon_txt_domain,
) -> str:
    """
    Return a URL which delegates carbon.txt using a DNS TXT record,
    Ensure the delegated URL responds with a valid carbon.txt and a 200 response.
    """
    return f"https://{mocked_dns_delegating_carbon_txt_domain}/carbon.txt"


@pytest.fixture(
    params=[
        pytest.param(
            "",
            marks=pytest.mark.httpx_mock(
                should_mock=lambda request: request.url.host.endswith(
                    "withcarbontxt.example.com"
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
    domain = "non-existent.withcarbontxt.example.com"
    url = f"https://{domain}/carbon.txt"
    well_known_url = f"https://{domain}/.well-known/carbon.txt"
    httpx_mock.add_response(
        url=url,
        status_code=404,
        is_reusable=True,
        is_optional=True,
    )
    httpx_mock.add_response(
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
