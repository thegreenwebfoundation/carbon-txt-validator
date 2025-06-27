import pytest

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
            result.uri == "https://managed-service.withcarbontxt.example.com/carbon.txt"
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
            result.uri == "https://managed-service.withcarbontxt.example.com/carbon.txt"
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
            result.uri == "https://managed-service.withcarbontxt.example.com/carbon.txt"
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
            == "https://second-managed-service.withcarbontxt.example.com/carbon.txt"
        )

        # We get back a result that is delegated using DNS
        # TODO: This needs to be thought through some more.
        # this case be represented?
        assert result.delegation_method == "dns"
