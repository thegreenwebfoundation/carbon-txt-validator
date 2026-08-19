from datetime import date

import pytest

from carbon_txt import build_carbontxt_file
from carbon_txt.validators import CarbonTxtValidator

file = build_carbontxt_file(
    {
        "version": "0.4",
        "last_updated": date.fromisoformat("2025-01-01"),
        "org": {
            "disclosures": [
                {
                    "url": "https://example.com/page",
                    "doc_type": "web-page",
                    "title": "Web Page",
                    "domain": "example.com",
                }
            ]
        },
        "upstream": {
            "services": [
                {"domain": "example.com", "service_type": "virtual-private-servers"}
            ]
        },
    }
)


def test_to_toml_without_comment():
    """
    Given a valid carbon.txt syntax tree
    When I convert it to TOML
    It should correctly serialize all the data in the file
    """
    assert CarbonTxtValidator().validate_contents(file.to_toml()).result == file


def test_to_toml_with_comment():
    """
    Given a valid carbon.txt syntax tree
    When I convert it to TOML
    And I pass an optional header comment
    It should include the header comment at the top of the file
    """
    comment = "This file was automatically generated"
    contents = file.to_toml(header_comment=comment)
    assert contents.split("\n")[0] == f"# {comment}"


@pytest.fixture()
def version_0_6_file_with_certification_schemes():
    """
    A version 0.6 carbon.txt tree exercising the new certification-scheme
    fields: a declared scheme, plus disclosure-level description and
    certification_schemes references.
    """
    return build_carbontxt_file(
        {
            "version": "0.6",
            "last_updated": date.fromisoformat("2026-01-01"),
            "org": {
                "certification_schemes": [
                    {
                        "id": "b-corp",
                        "url": "https://example.com/bcorp",
                        "title": "B Corp",
                        "description": "A B Corp certified org",
                    }
                ],
                "disclosures": [
                    {
                        "url": "https://example.com/cert.pdf",
                        "doc_type": "certificate",
                        "description": "Our B Corp certificate",
                        "certification_schemes": ["b-corp"],
                    }
                ],
            },
        }
    )


def test_version_0_6_round_trip_retains_certification_schemes(
    version_0_6_file_with_certification_schemes,
):
    """
    Serialising a v0.6 file to TOML and back should not silently drop the
    new certification-scheme fields.
    This because the v0.6 Organisation and Disclosure don't add the
    new fields to `toml_fields`.
    """
    toml = version_0_6_file_with_certification_schemes.to_toml()
    result = CarbonTxtValidator().validate_contents(toml).result
    org = result.org

    assert org.certification_schemes is not None, "our certication_schemes should be here on the org"
    assert org.certification_schemes[0].id == "b-corp"
    assert org.certification_schemes[0].title == "B Corp"
    assert org.certification_schemes[0].description == "A B Corp certified org"

    disclosure = org.disclosures[0]
    assert disclosure.description == "Our B Corp certificate"
    assert disclosure.certification_schemes == ["b-corp"]
