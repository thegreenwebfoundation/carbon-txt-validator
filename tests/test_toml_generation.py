from datetime import date

from carbon_txt import build_from_dict
from carbon_txt.validators import CarbonTxtValidator

file = build_from_dict(
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
