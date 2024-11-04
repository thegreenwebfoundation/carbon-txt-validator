from carbon_txt.finders import FileFinder


class TestFinder:
    def test_looking_up_domain_simple(self):
        """
        Look up a domain with a carbon.txt file based on the domain, and return the carbon.txt file URL
        """

        finder = FileFinder()

        # Given a domain with

        # When we pass a domain
        result = finder.resolve_domain("used-in-tests.carbontxt.org")

        # We get back the URI of the carbon.txt file to lookup
        assert result == "https://used-in-tests.carbontxt.org/carbon.txt"

    def test_looking_up_uri_simple(self):
        """Looking up a domain with a carbon.txt file"""

        finder = FileFinder()

        # Given a domain with

        # When we pass a domain
        result = finder.resolve_uri("https://used-in-tests.carbontxt.org/carbon.txt")

        # We get back the URI of the carbon.txt file to lookup
        assert result == "https://used-in-tests.carbontxt.org/carbon.txt"
