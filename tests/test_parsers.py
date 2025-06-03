from carbon_txt.parsers_toml import CarbonTxtParser
from carbon_txt.exceptions import NotParseableTOMLButHTML
import pytest

parser = CarbonTxtParser()


class TestParseCarbonTxt:
    def test_parse_toml(self, minimal_carbon_txt_org):
        """
        Test parsing a minimal carbon.txt file
        """
        parsed = parser.parse_toml(minimal_carbon_txt_org, logs=[])
        assert "upstream" in parsed
        assert "org" in parsed
        assert "services" in parsed["upstream"]
        assert "disclosures" in parsed["org"]
        assert len(parsed["upstream"]["services"]) == 0
        assert len(parsed["org"]["disclosures"]) == 1

    def test_parse_toml_short(self, shorter_carbon_txt_string):
        """
        Test parsing a minimal carbon.txt file
        """
        parsed = parser.parse_toml(shorter_carbon_txt_string, logs=[])
        assert parsed
        assert "upstream" in parsed
        assert "org" in parsed
        assert "services" in parsed["upstream"]
        assert "disclosures" in parsed["org"]
        assert len(parsed["upstream"]["services"]) == 2
        assert len(parsed["org"]["disclosures"]) == 1

    def test_parse_toml_minimal(self, minimal_carbon_txt_org):
        """
        Test parsing a minimal carbon.txt file
        """
        parsed = parser.parse_toml(minimal_carbon_txt_org, logs=[])
        assert parsed
        assert "upstream" in parsed
        assert "org" in parsed
        assert "services" in parsed["upstream"]
        assert "disclosures" in parsed["org"]
        assert len(parsed["upstream"]["services"]) == 0
        assert len(parsed["org"]["disclosures"]) == 1
        assert (
            parsed["org"]["disclosures"][0]["domain"] == "used-in-tests.carbontxt.org"
        )
        assert parsed["org"]["disclosures"][0]["doc_type"] == "sustainability-page"
        assert (
            parsed["org"]["disclosures"][0]["url"]
            == "https://used-in-tests.carbontxt.org/our-climate-record"
        )

    @pytest.mark.parametrize(
        "carbon_txt_fixture",
        [
            "minimal_carbon_txt_org",
            "shorter_carbon_txt_string",
            "multi_domain_carbon_txt_string",
        ],
    )
    def test_parse_to_carbon_txt_data_structure(self, carbon_txt_fixture, request):
        """ """

        # request is a magic pytest fixture that can be used to access other fixtures
        carbon_txt_content = request.getfixturevalue(carbon_txt_fixture)
        parsed = parser.parse_toml(carbon_txt_content, logs=[])

        # errors are triggered on instantiation, so if the parsed data
        # validates, then the test passes
        parser.validate_as_carbon_txt(parsed, logs=[])

    def test_parse_invalid_toml_but_valid_html(self, valid_html_not_found_page):
        """
        Do we raise an appropriate exception when we were expecting TOML,
        but got a valid HTML page instead?

        like with a 404 or 200 index html page?
        """

        # Test passing HTML content to the parser raises NotTOMLButHTML exception
        with pytest.raises(NotParseableTOMLButHTML) as excinfo:
            parser.parse_toml(valid_html_not_found_page, logs=[])
            assert excinfo.type.__name__ == "NotParseableTOMLButHTML"
