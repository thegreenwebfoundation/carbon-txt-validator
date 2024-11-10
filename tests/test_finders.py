from carbon_txt.finders import FileFinder


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

    def test_looking_up_uri_with_delegation_using_via(self):
        """
        Looking up a domain that has a 'via' http header should result
        in us returning the URL in the via header, not the origina looked up URL
        """

        finder = FileFinder()

        # Given our origina domain with
        hosted_domain = "https://hosted.carbontxt.org/carbon.txt"
        via_domain = "https://managed-service.carbontxt.org/carbon.txt"

        # When we pass a domain
        result = finder.resolve_uri(hosted_domain)

        # We get back the URI of the carbon.txt file to lookup
        assert result == via_domain
