import pytest
import re
from carbon_txt.finders import FileFinder  # type: ignore
from carbon_txt.exceptions import UnreachableCarbonTxtFile  # type: ignore


class TestFinder:
    def test_looking_up_domain_simple(self, mocked_carbon_txt_domain):
        """
        Look up a domain with a carbon.txt file based on the domain, and return the carbon.txt file URL
        """

        finder = FileFinder()

        # Given a domain

        # When we pass a domain
        result = finder.resolve_domain(mocked_carbon_txt_domain)

        # We get back the URI of the carbon.txt file to lookup
        assert result.uri == f"https://{mocked_carbon_txt_domain}/carbon.txt"

        # We get back a result that is not delegated
        assert result.delegation_method is None

    def test_looking_up_domain_with_delegation_using_dns(
        self, mocked_dns_delegating_carbon_txt_domain
    ):
        """
        Looking up a domain that has a carbon.txt DNS TXT record
        should delegate us to the correct URL in that TXT record,
        """
        finder = FileFinder()

        # Given a domain

        # When we pass a domain
        result = finder.resolve_domain(mocked_dns_delegating_carbon_txt_domain)

        # We get back the URI of the carbon.txt file to lookup
        assert (
            result.uri == "https://managed-service.example.com/carbon.txt"
        )

        # We get back a result that is delegated using DNS
        assert result.delegation_method == "dns"

    def test_looking_up_domain_with_delegation_using_http(
        self, mocked_http_delegating_carbon_txt_domain
    ):
        """
        Looking up a domain that has a "CarbonTxt-Location" HTTP header
        should delegate us to the correct URL in that header,
        """
        finder = FileFinder()

        # Given a domain

        # When we pass a domain
        result = finder.resolve_domain(mocked_http_delegating_carbon_txt_domain)

        # We get back the URI of the carbon.txt file to lookup
        assert (
            result.uri == "https://managed-service.example.com/carbon.txt"
        )

        # We get back a result that is delegated using HTTP
        assert result.delegation_method == "http"

    def test_looking_up_uri_simple(self, mocked_carbon_txt_url):
        """Looking up a domain with a carbon.txt file"""

        finder = FileFinder()

        # Given a domain with carbon.txt extension

        # When we pass a domain
        result = finder.resolve_uri(mocked_carbon_txt_url)

        # We get back the URI of the carbon.txt file to lookup
        assert result.uri == mocked_carbon_txt_url

        # We get back a result that is not delegated
        assert result.delegation_method is None

    def test_looking_up_uri_with_delegation_using_dns(
        self, mocked_dns_delegating_carbon_txt_url
    ):
        """
        Looking up a specific carbon.txt file URL at a domain that has a
        carbon.txt DNS TXT record should NOT delegate us to the domain in
        the txt record
        """
        finder = FileFinder()
        with pytest.raises(UnreachableCarbonTxtFile):
            finder.resolve_uri(mocked_dns_delegating_carbon_txt_url)

    def test_looking_up_uri_with_delegation_using_http_headder(
        self, mocked_http_delegating_carbon_txt_url
    ):
        """
         Looking up a specific carbon.txt file URL at a domain that delegates
         using the HTTP CarbonTxt-Location header shoult NOT delegate us to the domain in
        the header
        """

        finder = FileFinder()

        # When we pass a domain
        result = finder.resolve_uri(mocked_http_delegating_carbon_txt_url)

        # We get back the URI of the carbon.txt file to lookup
        assert result.uri == mocked_http_delegating_carbon_txt_url

        # We get back a result that is not delegated
        assert result.delegation_method is None

    def test_looking_up_uri_with_no_carbon_txt_at_all(self, mocked_404_carbon_txt_url):
        """
        Looking up a domain that has no carbon.txt file should raise an exception
        """
        finder = FileFinder()
        with pytest.raises(UnreachableCarbonTxtFile):
            finder.resolve_uri(mocked_404_carbon_txt_url)

    def test_fetch_carbon_txt_file(self, mocked_carbon_txt_url):
        finder = FileFinder()

        result = finder.fetch_carbon_txt_file(mocked_carbon_txt_url)
        # We get back the carbon.txt file contents which should be a string
        # of at least 180 characters
        assert len(result) > 180
        assert isinstance(result, str)

    def test_fetch_carbon_txt_file_fails(self, mocked_404_carbon_txt_url):
        """
        When looking up a carbon.txt file fails, we should raise a helpful exception
        """
        finder = FileFinder()

        with pytest.raises(UnreachableCarbonTxtFile):
            finder.fetch_carbon_txt_file(mocked_404_carbon_txt_url)

    def test_file_takes_precedence_over_dns(
        self, mocked_carbon_txt_domain_with_file_and_dns_delegation
    ):
        """
        When a domain has a carbon.txt file in the root directory, and also a DNS delegation record,
        the DNS record should take precedence.
        """
        finder = FileFinder()

        # Given a domain with both a DNS delegation record and a carbon.txt

        # When we pass a domain
        result = finder.resolve_domain(
            mocked_carbon_txt_domain_with_file_and_dns_delegation
        )

        # We get back the URI of the carbon.txt file from the DNS record
        assert (
            result.uri == "https://managed-service.example.com/carbon.txt"
        )

        # We get back a result that is delegated using DNS
        assert result.delegation_method == "dns"

    def test_file_takes_precedence_over_http_header(
        self, mocked_carbon_txt_domain_with_file_and_http_delegation
    ):
        """
        When a domain has both a carbon.txt file, and an HTTP delegation
        header, the file should take precedence.
        """
        finder = FileFinder()

        # Given a domain with both a hosted carbon.txt file and an HTTP
        # delegation header

        # When we pass a domain
        result = finder.resolve_domain(
            mocked_carbon_txt_domain_with_file_and_http_delegation
        )

        # We get back the URI of the hosted carbon.txt file
        assert (
            result.uri
            == f"https://{mocked_carbon_txt_domain_with_file_and_http_delegation}/carbon.txt"
        )

        # We get back a result that is not delegated
        assert result.delegation_method is None

    def test_recursive_delegation(
        self, mocked_carbon_txt_domain_with_recursive_delegation
    ):
        """
        When a domain delegates to another domain, rather than a full carbon.txt url,
        the delegation following process should be applied recursively until a full
        carbon.txt URL is found.
        """
        finder = FileFinder()

        # Given a domain which delegates carbon.txt to a first manaaged service, which in
        # turn delegates to a second managed service

        # When we pass a domain
        result = finder.resolve_domain(
            mocked_carbon_txt_domain_with_recursive_delegation
        )

        # We get back the URI of the carbon.txt file at the second managed service
        assert (
            result.uri
            == "https://second-managed-service.example.com/carbon.txt"
        )

        # We get back a result that is delegated using DNS
        # TODO: This needs to be thought through some more.
        # this case be represented?
        assert result.delegation_method == "dns"

    def test_passing_timeout_to_finder(self, mocked_carbon_txt_domain, httpx_mock):
        """
        Passing an http timeout to the finder constructor passes it
        through to any httpx requests made
        """

        # Given a FileFinder with a Timeout
        timeout = 2.0
        finder = FileFinder(http_timeout=timeout)

        # When we pass a domain
        finder.resolve_domain(mocked_carbon_txt_domain)

        # Then the http transport library should be called with the timeout.
        for request in httpx_mock.get_requests():
            assert set(request.extensions["timeout"].values()) == set([timeout])

    def test_passing_user_agent_to_finder(self, mocked_carbon_txt_domain, httpx_mock):
        """
        Passing a user agent to the finder constructor passes it
        through to any httpx requests made
        """

        # Given a FileFinder with a UserAgent
        user_agent = "MyCarbonTxtApp/1.0"
        finder = FileFinder(http_user_agent=user_agent)

        # When we pass a domain
        finder.resolve_domain(mocked_carbon_txt_domain)

        # Then the http transport library should be called with the timeout.
        for request in httpx_mock.get_requests():
            assert request.headers["User-Agent"] == user_agent

    def test_default_user_agent(self, mocked_carbon_txt_domain, httpx_mock):
        """
        The User agent defaults to a descriptive string with the version number and a URL.
        """

        # Given a FileFinder with a UserAgent
        user_agent_re = re.compile(
            "CarbonTxtValidator/[0-9]+\\.[0-9]+\\.[0-9]+ \\(https://carbontxt.org/tools/validator\\)"
        )
        finder = FileFinder()

        # When we pass a domain
        finder.resolve_domain(mocked_carbon_txt_domain)

        # Then the http transport library should be called with the timeout.
        for request in httpx_mock.get_requests():
            assert re.match(user_agent_re, request.headers["User-Agent"])

    def test_looking_up_a_www_subdomain_unsuccesfully_falls_back_to_tld(self, mocked_carbon_txt_domain):
        # Given a FileFinder and a TLD with a carbon.txt
        finder = FileFinder()

        # When we pass the www subdomain of the TLD
        result = finder.resolve_domain("www." + mocked_carbon_txt_domain)

        # Then we get back the URI of the carbon.txt file at the TLD
        assert result.uri == f"https://{mocked_carbon_txt_domain}/carbon.txt"


    def test_looking_up_a_tld_unsuccesfully_falls_back_to_www_subdomain(self, mocked_domain_with_www_fallback):
        # Given a FileFinder and a TLD whose www subdomain has a carbon.txt
        finder = FileFinder()

        # When we pass the TLD
        result = finder.resolve_domain(mocked_domain_with_www_fallback)

        # Then we get back the URI of the carbon.txt file at the www. subdomain
        assert result.uri == f"https://www.{mocked_domain_with_www_fallback}/carbon.txt"


    def test_looking_up_a_tld_succesfully_does_not_fall_back(self, mocked_carbon_txt_domain, httpx_mock):
        # Given a FileFinder and a TLD with a carbon.txt
        finder = FileFinder()

        # When we pass the TLD itself
        result = finder.resolve_domain(mocked_carbon_txt_domain)

        # Then we get back the URI of the carbon.txt file at the TLD
        assert result.uri == f"https://{mocked_carbon_txt_domain}/carbon.txt"

        # And the www subdomain should not be checked
        assert f"www.{mocked_carbon_txt_domain}" not in [str(r.url) for r in httpx_mock.get_requests()]

    def test_looking_up_a_www_subdomain_succesfully_does_not_fall_back(self, mocked_domain_with_www_fallback, httpx_mock):
        # Given a FileFinder and a TLD whose www subdomain has a carbon.txt
        finder = FileFinder()

        # When we pass the www subdomain
        result = finder.resolve_domain(f"www.{mocked_domain_with_www_fallback}")

        # Then we get back the URI of the carbon.txt file at the www. subdomain
        assert result.uri == f"https://www.{mocked_domain_with_www_fallback}/carbon.txt"

        # And the TLD should not be checked
        assert mocked_domain_with_www_fallback not in [str(r.url) for r in httpx_mock.get_requests()]

    def test_looking_up_other_subdomain_does_not_fallback(self, mocked_carbon_txt_domain, httpx_mock):
        # Given a FileFinder and a TLD whose www subdomain has a carbon.txt
        finder = FileFinder()

        # When we pass any other non www. subdomain
        # Then no carbon.txt is found
        with pytest.raises(UnreachableCarbonTxtFile):
            finder.resolve_domain(f"other-subdomain.{mocked_carbon_txt_domain}")

        # And the TLD should not be checked
        assert mocked_carbon_txt_domain not in [str(r.url) for r in httpx_mock.get_requests()]
