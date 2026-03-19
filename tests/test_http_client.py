import re
from carbon_txt.http_client import HTTPClient


class TestHttpClient:
    def test_passing_timeout_to_finder(self, mocked_carbon_txt_domain, httpx_mock):
        """
        Passing an http timeout to the finder constructor passes it
        through to any httpx requests made
        """

        # Given an HTTPClient with a Timeout
        timeout = 2.0
        client = HTTPClient(http_timeout=timeout)

        # When we make a request
        client.get(f"https://{mocked_carbon_txt_domain}/carbon.txt")

        # Then the http transport library should be called with the timeout.
        for request in httpx_mock.get_requests():
            assert set(request.extensions["timeout"].values()) == set([timeout])

    def test_passing_user_agent_to_finder(self, mocked_carbon_txt_domain, httpx_mock):
        """
        Passing a user agent to the finder constructor passes it
        through to any httpx requests made
        """

        # Given an HTTPClient with a UserAgent
        user_agent = "MyCarbonTxtApp/1.0"
        client = HTTPClient(http_user_agent=user_agent)

        # When we make a request
        client.get(f"https://{mocked_carbon_txt_domain}/carbon.txt")

        # Then the http transport library should be called with the timeout.
        for request in httpx_mock.get_requests():
            assert request.headers["User-Agent"] == user_agent

    def test_default_user_agent(self, mocked_carbon_txt_domain, httpx_mock):
        """
        The User agent defaults to a descriptive string with the version number and a URL.
        """

        # Given an HTTPClient without a UserAgent
        user_agent_re = re.compile(
            "CarbonTxtValidator/[0-9]+\\.[0-9]+\\.[0-9]+ \\(https://carbontxt.org/tools/validator\\)"
        )
        client = HTTPClient()

        # When we make a request
        client.get(f"https://{mocked_carbon_txt_domain}/carbon.txt")

        # Then the http transport library should be called with the timeout.
        for request in httpx_mock.get_requests():
            assert re.match(user_agent_re, request.headers["User-Agent"])
