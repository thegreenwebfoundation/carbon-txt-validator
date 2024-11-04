from carbon_txt.parsers_toml import CarbonTxtParser
import pytest

parser = CarbonTxtParser()


class TestParseCarbonTxt:
    def test_parse_toml(self, minimal_carbon_txt_org):
        """
        Test parsing a minimal carbon.txt file
        """
        parsed = parser.parse_toml(minimal_carbon_txt_org)
        assert "upstream" in parsed
        assert "org" in parsed
        assert "providers" in parsed["upstream"]
        assert "credentials" in parsed["org"]
        assert len(parsed["upstream"]["providers"]) == 0
        assert len(parsed["org"]["credentials"]) == 1

    def test_parse_toml_short(self, shorter_carbon_txt_string):
        """
        Test parsing a minimal carbon.txt file
        """
        parsed = parser.parse_toml(shorter_carbon_txt_string)
        assert parsed
        assert "upstream" in parsed
        assert "org" in parsed
        assert "providers" in parsed["upstream"]
        assert "credentials" in parsed["org"]
        assert len(parsed["upstream"]["providers"]) == 2
        assert len(parsed["org"]["credentials"]) == 1

    def test_parse_toml_minimal(self, minimal_carbon_txt_org):
        """
        Test parsing a minimal carbon.txt file
        """
        parsed = parser.parse_toml(minimal_carbon_txt_org)
        assert parsed
        assert "upstream" in parsed
        assert "org" in parsed
        assert "providers" in parsed["upstream"]
        assert "credentials" in parsed["org"]
        assert len(parsed["upstream"]["providers"]) == 0
        assert len(parsed["org"]["credentials"]) == 1
        assert (
            parsed["org"]["credentials"][0]["domain"] == "used-in-tests.carbontxt.org"
        )
        assert parsed["org"]["credentials"][0]["doctype"] == "sustainability-page"
        assert (
            parsed["org"]["credentials"][0]["url"]
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
        parsed = parser.parse_toml(carbon_txt_content)

        # errors are triggered on instantiation, so if the parsed data
        # validates, then the test passes
        parser.validate_as_carbon_txt(parsed)
