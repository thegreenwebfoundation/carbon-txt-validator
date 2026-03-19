import pathlib
import unittest

import pytest
from httpx import HTTPError

from carbon_txt.processors import GreenwebAIModelCardProcessor


def model_card_fixture(filename):
    file_path = pathlib.Path(__file__).parent / "fixtures" / "ai_model_cards" / filename
    with open(file_path) as file:
        return file.read()


def get_result(results, short_code):
    for result in results:
        if result.short_code == short_code:
            return result


class TestGreenwebAIModelCardProcessor(unittest.TestCase):
    # This needs to be a TestCase subclass, in order to access
    # self.assertRaises in the http response code test method.
    @pytest.fixture(autouse=True)
    def setup_httpx_mock(self, httpx_mock):
        self.httpx_mock = httpx_mock

    def setup_model_card_fixture_url(
        self, filename, content_type="text/markdown", status_code=200
    ):
        model_card = model_card_fixture(filename)
        url = f"https://example.com/{filename}"
        self.httpx_mock.add_response(
            method="GET",
            url=url,
            content=model_card,
            headers={"content-type": content_type},
            status_code=status_code,
        )
        return url

    def test_parses_model_card_with_complete_emissions_section(self):
        url = self.setup_model_card_fixture_url("complete.md")
        processor = GreenwebAIModelCardProcessor(card_url=url)
        results = processor.get_co2_eq_emissions()
        assert get_result(results, "emissions").value == 123.456
        assert get_result(results, "source").value == "codecarbon"
        assert get_result(results, "training_type").value == "fine-tuning"
        assert get_result(results, "hardware_used").value == "NVIDIA RTX-4060"
        assert (
            get_result(results, "geographical_location").value
            == "Amsterdam, Netherlands"
        )

    def test_parses_model_card_with_partial_emissions_section(self):
        url = self.setup_model_card_fixture_url("partial.md")
        processor = GreenwebAIModelCardProcessor(card_url=url)
        results = processor.get_co2_eq_emissions()
        assert get_result(results, "emissions").value == 123.456
        assert get_result(results, "source").value == "codecarbon"
        for field in GreenwebAIModelCardProcessor.FIELDS:
            if field.short_code not in ("emissions", "source"):
                assert get_result(results, field.short_code).value is None
                assert (
                    get_result(results, field.short_code).message
                    == f"This AI model card does not include the {field.short_code} field."
                )

    def test_does_not_include_extra_nonstandard_fields(self):
        url = self.setup_model_card_fixture_url("extra_fields.md")
        processor = GreenwebAIModelCardProcessor(card_url=url)
        results = processor.get_co2_eq_emissions()
        assert get_result(results, "emissions").value == 123.456
        assert get_result(results, "energy_used") is None

    def test_raises_error_when_no_emissions_section(self):
        url = self.setup_model_card_fixture_url("no_co2_eq_emissions.md")
        processor = GreenwebAIModelCardProcessor(card_url=url)
        results = processor.get_co2_eq_emissions()
        for field in GreenwebAIModelCardProcessor.FIELDS:
            assert get_result(results, field.short_code).value is None
            assert (
                get_result(results, field.short_code).message
                == "This AI model card does not include a co2_eq_emissions section."
            )

    def test_raises_error_when_no_front_matter(self):
        url = self.setup_model_card_fixture_url("no_front_matter.md")
        processor = GreenwebAIModelCardProcessor(card_url=url)
        results = processor.get_co2_eq_emissions()
        for field in GreenwebAIModelCardProcessor.FIELDS:
            assert get_result(results, field.short_code).value is None
            assert (
                get_result(results, field.short_code).message
                == "This AI model card does not include a co2_eq_emissions section."
            )

    def test_raises_error_for_badly_formatted_emissions_section(self):
        url = self.setup_model_card_fixture_url("badly_formatted_co2_section.md")
        processor = GreenwebAIModelCardProcessor(card_url=url)
        results = processor.get_co2_eq_emissions()
        for field in GreenwebAIModelCardProcessor.FIELDS:
            assert get_result(results, field.short_code).value is None
            assert (
                get_result(results, field.short_code).message
                == "This AI model card has an incorrectly formatted co2_eq_emissions section."
            )

    def test_raises_error_when_not_markdown(self):
        url = self.setup_model_card_fixture_url(
            "not_markdown.html", content_type="text/html"
        )
        processor = GreenwebAIModelCardProcessor(card_url=url)
        results = processor.get_co2_eq_emissions()
        for field in GreenwebAIModelCardProcessor.FIELDS:
            assert get_result(results, field.short_code).value is None
            assert (
                get_result(results, field.short_code).message
                == "This AI model card is not in markdown format. Please use the URL to the markdown source of the model card."
            )

    def test_raises_error_on_http_error_response_code(self):
        url = self.setup_model_card_fixture_url("complete.md", status_code=404)
        processor = GreenwebAIModelCardProcessor(card_url=url)
        with self.assertRaises(HTTPError):
            processor.get_co2_eq_emissions()
