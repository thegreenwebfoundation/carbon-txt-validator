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
        assert result == f"https://{mocked_carbon_txt_domain}/carbon.txt"

    def test_looking_up_domain_with_delegation_using_dns(
        self, mocked_dns_delegating_carbon_txt_domain
    ):
        """
        Looking up a domain that has a carbon.txt DNS TXT record
        should delegate us to the correct URL in that TXT record, overriding
        the original domain
        """
        finder = FileFinder()

        # Given a domain

        # When we pass a domain
        result = finder.resolve_domain(mocked_dns_delegating_carbon_txt_domain)

        # We get back the URI of the carbon.txt file to lookup
        assert result == "https://managed-service.withcarbontxt.example.com/carbon.txt"

    def test_looking_up_domain_with_delegation_using_http(
        self, mocked_http_delegating_carbon_txt_domain
    ):
        """
        Looking up a domain that has a "via" http header
        should delegate us to the correct URL in that header, overriding
        the original domain
        """
        finder = FileFinder()

        # Given a domain

        # When we pass a domain
        result = finder.resolve_domain(mocked_http_delegating_carbon_txt_domain)

        # We get back the URI of the carbon.txt file to lookup
        assert result == "https://managed-service.withcarbontxt.example.com/carbon.txt"

    def test_looking_up_uri_simple(self, mocked_carbon_txt_url):
        """Looking up a domain with a carbon.txt file"""

        finder = FileFinder()

        # Given a domain with carbon.txt extension

        # When we pass a domain
        result = finder.resolve_uri(mocked_carbon_txt_url)

        # We get back the URI of the carbon.txt file to lookup
        assert result == mocked_carbon_txt_url

    def test_looking_up_uri_with_delegation_using_dns(
        self, mocked_dns_delegating_carbon_txt_url
    ):
        """
        Looking up a specific carbon.txt file URL at a domain that has a
        carbon.txt DNS TXT record should NOT delegate us to the domain in
        the txt record
        """
        finder = FileFinder()
        result = finder.resolve_uri(mocked_dns_delegating_carbon_txt_url)
        assert result == mocked_dns_delegating_carbon_txt_url

    def test_looking_up_uri_with_delegation_using_via(
        self, mocked_http_delegating_carbon_txt_url
    ):
        """
         Looking up a specific carbon.txt file URL at a domain that delegates
         using the HTTP via header shoult NOT delegate us to the domain in

        the via header
        """

        finder = FileFinder()

        # When we pass a domain
        result = finder.resolve_uri(mocked_http_delegating_carbon_txt_url)

        # We get back the URI of the carbon.txt file to lookup
        assert result == mocked_http_delegating_carbon_txt_url

    def test_looking_up_uri_with_no_carbon_txt_at_all(self, mocked_404_carbon_txt_url):
        """
        Looking up a domain that has no carbon.txt file should still return
        the uri to check.
        """
        finder = FileFinder()

        assert (
            finder.resolve_uri(mocked_404_carbon_txt_url) == mocked_404_carbon_txt_url
        )

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
