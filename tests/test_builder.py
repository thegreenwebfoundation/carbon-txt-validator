import pytest
from datetime import date

from pydantic import ValidationError

from carbon_txt import build_carbontxt_file
from carbon_txt.schemas import LATEST_VERSION, VERSIONS, InvalidVersionError


def test_disclosures_are_passed():
    """
    Given a carbon.txt data dictionary with disclosures
    When I create a carbon.txt file from the dictionary
    The disclosures are properly created.
    """
    data = {
        "org": {
            "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
        }
    }
    result = build_carbontxt_file(data)
    assert result.org.disclosures[0].url == data["org"]["disclosures"][0]["url"]
    assert (
        result.org.disclosures[0].doc_type == data["org"]["disclosures"][0]["doc_type"]
    )


def test_services_are_passed():
    """
    Given a carbon.txt data dictionary with services
    When I create a carbon.txt file from the dictionary
    The services are properly created.
    """
    data = {
        "org": {
            "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
        },
        "upstream": {
            "services": [
                {"domain": "example.com", "service_type": "virtual-private-servers"}
            ]
        },
    }
    result = build_carbontxt_file(data)
    assert (
        result.upstream.services[0].domain == data["upstream"]["services"][0]["domain"]
    )
    assert (
        result.upstream.services[0].service_type
        == data["upstream"]["services"][0]["service_type"]
    )


def test_validation_errors_are_raised():
    """
    Given a carbon.txt data dictionary which is invalid
    When I create a carbon.txt file from the dictionary
    A ValidationError is raised.
    """
    data = {
        "org": {"disclosures": []},
    }
    with pytest.raises(ValidationError):
        build_carbontxt_file(data)


def test_version_is_respected():
    """
    Given a carbon.txt data dictionary with an explicit version number
    When I create a carbon.txt file from the dictionary
    The version attribute is respected
    And the correct syntax class is used
    """
    data = {
        "version": "0.3",
        "org": {
            "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
        },
    }
    result = build_carbontxt_file(data)
    assert result.version == data["version"]
    assert isinstance(result, VERSIONS[data["version"]])


def test_latest_version_default():
    """
    Given a carbon.txt data dictionary with no version number
    When I create a carbon.txt file from the dictionary
    The version attribute is defaulted to the latest syntax version
    And the correct syntax class is used
    """
    data = {
        "org": {
            "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
        }
    }
    result = build_carbontxt_file(data)
    assert result.version == LATEST_VERSION
    assert isinstance(result, VERSIONS[LATEST_VERSION])


def test_invalid_version_raises_error():
    data = {
        "version": "0.1",
        "org": {
            "disclosures": [{"url": "https://example.com", "doc_type": "web-page"}]
        },
    }
    with pytest.raises(InvalidVersionError):
        build_carbontxt_file(data)


def test_last_updated_default():
    """
    Given a carbon.txt data dictionary with no last updated date
    When I create a carbon.txt file from the dictionary
    The last updated date is defaulted to the current day
    """
    data = {
        "org": {
            "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
        }
    }
    result = build_carbontxt_file(data)
    assert result.last_updated == date.today()


def test_last_updated_explicit_null():
    """
    Given a carbon.txt data dictionary with an explicit None as the last updated date
    When I create a carbon.txt file from the dictionary
    The last updated date is not set
    """
    data = {
        "last_updated": None,
        "org": {
            "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
        },
    }
    result = build_carbontxt_file(data)
    assert result.last_updated is None


def test_last_updated_explicit_date():
    """
    Given a carbon.txt data dictionary with an explicit last updated date
    When I create a carbon.txt file from the dictionary
    The last updated date is respected
    """
    data = {
        "last_updated": date.fromisoformat("2025-01-01"),
        "org": {
            "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
        },
    }
    result = build_carbontxt_file(data)
    assert result.last_updated == data["last_updated"]
