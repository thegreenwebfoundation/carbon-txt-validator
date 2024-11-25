import pytest

from carbon_txt.finders import FileFinder  # type: ignore
from carbon_txt.exceptions import UnreachableCarbonTxtFile  # type: ignore


class TestFinder:
    def test_looking_up_domain_simple(self):
        """
        Look up a domain with a carbon.txt file based on the domain, and return the carbon.txt file URL
        """

        finder = FileFinder()

        # Given a domain
        domain = "used-in-tests.carbontxt.org"

        # When we pass a domain
        result = finder.resolve_domain(domain)

        # We get back the URI of the carbon.txt file to lookup
        assert result == f"https://{domain}/carbon.txt"

    def test_looking_up_uri_simple(self):
        """Looking up a domain with a carbon.txt file"""

        finder = FileFinder()

        # Given a domain with carbon.txt extension
        carbon_txt_url = "https://used-in-tests.carbontxt.org/carbon.txt"

        # When we pass a domain
        result = finder.resolve_uri(carbon_txt_url)

        # We get back the URI of the carbon.txt file to lookup
        assert result == carbon_txt_url

    def test_looking_up_uri_with_delegation_using_dns(self):
        """
        Looking up a carbon.tx file at a domain that has a carbon.txt DNS TXT record
        should delegate us to the correct URL in that TXT record, overriding
        the original URL
        """
        finder = FileFinder()
        delegating_domain_url = (
            "https://delegating-with-txt-record.carbontxt.org/carbon.txt"
        )
        delegated_domain_url = "https://used-in-tests.carbontxt.org/carbon.txt"
        result = finder.resolve_uri(delegating_domain_url)
        assert result == delegated_domain_url

    def test_looking_up_uri_with_delegation_using_via(self):
        """
        Looking up a domain that has a 'via' http header should result
        in us returning the URL in the via header, not the originaL looked up URL
        """

        finder = FileFinder()

        # Given our original domain with
        hosted_domain_url = "https://hosted.carbontxt.org/carbon.txt"
        via_domain_url = "https://managed-service.carbontxt.org/carbon.txt"

        # When we pass a domain
        result = finder.resolve_uri(hosted_domain_url)

        # We get back the URI of the carbon.txt file to lookup
        assert result == via_domain_url

    def test_looking_up_uri_with_no_carbon_txt_at_all(self):
        """
        Looking up a domain that has no carbon.txt file should still return
        the uri to check.
        """
        finder = FileFinder()
        no_carbon_txt_url = "https://has-no.carbontxt.org/carbon.txt"

        assert finder.resolve_uri(no_carbon_txt_url) == no_carbon_txt_url

    def test_fetch_carbon_txt_file(self):
        finder = FileFinder()
        no_carbon_txt_url = "https://used-in-tests.carbontxt.org/carbon.txt"

        result = finder.fetch_carbon_txt_file(no_carbon_txt_url)
        # We get back the carbon.txt file contents which should be a string
        # of at least 180 characters
        assert len(result) > 180
        assert isinstance(result, str)

    @pytest.mark.skip(
        reason="This test is not yet implemented. Implement it once we add pytest-httpx"
    )
    def test_fetch_carbon_txt_file_fails(self):
        """
        When looking up a carbon.txt file fails, we should raise a helpful exception
        """
        finder = FileFinder()
        no_carbon_txt_url = "https://does-not-matter.carbontxt.org/carbon.txt"

        with pytest.raises(UnreachableCarbonTxtFile):
            finder.fetch_carbon_txt_file(no_carbon_txt_url)
