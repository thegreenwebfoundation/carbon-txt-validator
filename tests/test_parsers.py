import pytest
from pydantic import ValidationError

from carbon_txt.exceptions import NotParseableTOMLButHTML
from carbon_txt.parsers_toml import CarbonTxtParser

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
        ],
    )
    def test_parse_to_carbon_txt_data_structure(self, carbon_txt_fixture, request):
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

    def test_parse_version_0_2(self, version_0_2_carbon_txt_full):
        parsed = parser.parse_toml(version_0_2_carbon_txt_full, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.2"

    def test_parse_version_0_2_no_disclosure_domain(
        self, version_0_2_carbon_txt_no_disclosure_domain
    ):
        parsed = parser.parse_toml(version_0_2_carbon_txt_no_disclosure_domain, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.2"

    def test_parse_version_0_2_no_explicit_version(
        self, version_0_2_carbon_txt_no_explicit_version
    ):
        parsed = parser.parse_toml(version_0_2_carbon_txt_no_explicit_version, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.2"

    def test_parse_version_0_2_no_upstreams(self, version_0_2_carbon_txt_no_upstreams):
        parsed = parser.parse_toml(version_0_2_carbon_txt_no_upstreams, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.2"

    def test_parse_version_0_3(self, version_0_3_carbon_txt_full):
        parsed = parser.parse_toml(version_0_3_carbon_txt_full, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.3"

    def test_parse_version_0_3_no_last_updated(
        self, version_0_3_carbon_txt_no_last_updated
    ):
        parsed = parser.parse_toml(version_0_3_carbon_txt_no_last_updated, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.3"

    def test_parse_version_0_3_no_disclosure_domain(
        self, version_0_3_carbon_txt_no_disclosure_domain
    ):
        parsed = parser.parse_toml(version_0_3_carbon_txt_no_disclosure_domain, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.3"

    def test_parse_version_0_3_no_disclosure_valid_until(
        self, version_0_3_carbon_txt_no_disclosure_valid_until
    ):
        parsed = parser.parse_toml(
            version_0_3_carbon_txt_no_disclosure_valid_until, logs=[]
        )
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.3"

    def test_parse_version_0_3_no_upstreams(self, version_0_3_carbon_txt_no_upstreams):
        parsed = parser.parse_toml(version_0_3_carbon_txt_no_upstreams, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.3"

    def test_parse_version_0_4(self, version_0_4_carbon_txt_full):
        parsed = parser.parse_toml(version_0_4_carbon_txt_full, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.4"

    def test_parse_version_0_4_no_last_updated(
        self, version_0_4_carbon_txt_no_last_updated
    ):
        parsed = parser.parse_toml(version_0_4_carbon_txt_no_last_updated, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.4"

    def test_parse_version_0_4_no_disclosure_domain(
        self, version_0_4_carbon_txt_no_disclosure_domain
    ):
        parsed = parser.parse_toml(version_0_4_carbon_txt_no_disclosure_domain, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.4"

    def test_parse_version_0_4_no_disclosure_valid_until(
        self, version_0_4_carbon_txt_no_disclosure_valid_until
    ):
        parsed = parser.parse_toml(
            version_0_4_carbon_txt_no_disclosure_valid_until, logs=[]
        )
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.4"

    def test_parse_version_0_4_no_disclosure_title(
        self, version_0_4_carbon_txt_no_disclosure_title
    ):
        parsed = parser.parse_toml(version_0_4_carbon_txt_no_disclosure_title, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.4"

    def test_parse_version_0_4_no_upstreams(self, version_0_4_carbon_txt_no_upstreams):
        parsed = parser.parse_toml(version_0_4_carbon_txt_no_upstreams, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.4"

    def test_parse_version_0_5(self, version_0_5_carbon_txt_full):
        parsed = parser.parse_toml(version_0_5_carbon_txt_full, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.5"

    def test_parse_version_0_6(self, version_0_6_carbon_txt_full):
        """
        A version 0.6 carbon.txt with all fields defined is valid.
        """
        parsed = parser.parse_toml(version_0_6_carbon_txt_full, logs=[])
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.6"

    def test_parse_version_0_6_no_certification_scheme_description(
        self, version_0_6_carbon_txt_no_certification_scheme_description
    ):
        """
        A version 0.6 carbon.txt without a certification scheme description is still valid
        """
        parsed = parser.parse_toml(
            version_0_6_carbon_txt_no_certification_scheme_description, logs=[]
        )
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.6"

    def test_parse_version_0_6_no_certification_scheme_title(
        self, version_0_6_carbon_txt_no_certification_scheme_title
    ):
        """
        A version 0.6 carbon.txt without a certification scheme title is still valid
        """
        parsed = parser.parse_toml(
            version_0_6_carbon_txt_no_certification_scheme_title, logs=[]
        )
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.6"

    def test_parse_version_0_6_no_disclosure_description(
        self, version_0_6_carbon_txt_no_disclosure_description
    ):
        """
        A version 0.6 carbon.txt without a disclosure description is still valid
        """
        parsed = parser.parse_toml(
            version_0_6_carbon_txt_no_disclosure_description, logs=[]
        )
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.6"

    def test_parse_version_0_6_no_certification_schemes(
        self, version_0_6_carbon_txt_no_certification_schemes
    ):
        """
        A version 0.6 carbon.txt without any certification schemes is still valid
        """
        parsed = parser.parse_toml(
            version_0_6_carbon_txt_no_certification_schemes, logs=[]
        )
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.6"

    def test_parse_version_0_6_no_certification_scheme_title_or_description(
        self, version_0_6_carbon_txt_no_certification_scheme_title_or_description
    ):
        """
        A version 0.6 carbon.txt without a certification scheme title or description is still valid
        """
        parsed = parser.parse_toml(
            version_0_6_carbon_txt_no_certification_scheme_title_or_description, logs=[]
        )
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.6"

    def test_parse_version_0_6_multiple_certification_schemes(
        self, version_0_6_carbon_txt_multiple_certification_schemes
    ):
        """
        A version 0.6 carbon.txt with a disclosure referencing multiple certification schemes is still valid
        """
        parsed = parser.parse_toml(
            version_0_6_carbon_txt_multiple_certification_schemes, logs=[]
        )
        result = parser.validate_as_carbon_txt(parsed, logs=[])
        assert result.version == "0.6"

    def test_parse_version_0_6_no_certification_scheme_id(
        self, version_0_6_carbon_txt_no_certification_scheme_id
    ):
        """
        A version 0.6 carbon.txt without a certification scheme id is not valid
        """
        with pytest.raises(ValidationError):
            parsed = parser.parse_toml(
                version_0_6_carbon_txt_no_certification_scheme_id, logs=[]
            )
            parser.validate_as_carbon_txt(parsed, logs=[])

    def test_parse_version_0_6_no_certification_scheme_url(
        self, version_0_6_carbon_txt_no_certification_scheme_url
    ):
        """
        A version 0.6 carbon.txt without a certification scheme id is not valid
        """
        with pytest.raises(ValidationError):
            parsed = parser.parse_toml(
                version_0_6_carbon_txt_no_certification_scheme_url, logs=[]
            )
            parser.validate_as_carbon_txt(parsed, logs=[])

    def test_parse_version_0_6_duplicate_certification_scheme_id(
        self, version_0_6_carbon_txt_duplicate_certification_scheme_id
    ):
        """
        A version 0.6 carbon.txt with more than one certification scheme with the same id is not valid
        """
        with pytest.raises(ValidationError):
            parsed = parser.parse_toml(
                version_0_6_carbon_txt_duplicate_certification_scheme_id, logs=[]
            )
            parser.validate_as_carbon_txt(parsed, logs=[])

    def test_parse_version_0_6_undefined_certification_scheme_id(
        self, version_0_6_carbon_txt_undefined_certification_scheme_id
    ):
        """
        A version 0.6 carbon.txt with a disclosure that refers to an undefined certification scheme id is not valid
        """
        with pytest.raises(ValidationError):
            parsed = parser.parse_toml(
                version_0_6_carbon_txt_undefined_certification_scheme_id, logs=[]
            )
            parser.validate_as_carbon_txt(parsed, logs=[])
