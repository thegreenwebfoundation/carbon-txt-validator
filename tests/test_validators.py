from carbon_txt import validators  # type: ignore
import pytest
import pathlib


class TestCarbonTxtValidator:
    def test_validate_domain_without_carbon_txt(self, mocked_404_carbon_txt_domain):
        """
        This should show a failure, as there is no carbon.txt file at this domain
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_domain(f"https://{mocked_404_carbon_txt_domain}")
        assert not res.result
        assert res.exceptions

    def test_validate_url_without_carbon_txt(self, mocked_404_carbon_txt_url):
        """
        This should show a failure, as there is no carbon.txt file at this URL
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_url(mocked_404_carbon_txt_url)
        assert not res.result
        assert res.exceptions

    def test_validate_file_at_unreachable_url(self):
        """
        This should show a failure safely, as the URL is not reachable
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_url("https://does-not-matter.carbontxt.org/carbon.txt")

        assert not res.result
        assert res.exceptions

    def test_validate_file_at_with_multiple_validation_errors(self):
        """
        This should safely handle multiple validation errors gracefully
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_url(
            "https://used-in-tests-carbontxt.pages.dev/multiple-exceptions.carbon.txt"
        )

        assert not res.result
        assert res.exceptions

    @pytest.mark.skip(
        "This test is failing, as we now return meaningful exceptions from the csrd plugin. We need dummy plugin that returns empty results for csrd files"
    )
    def test_validate_file_with_correct_syntax_but_no_results_from_plugins(
        self, reset_plugin_registry, settings
    ):
        """
        When we try to validate a file that has correct syntax, but has no usable results coming
        back from the plugins, we should still get a successful result to show that the syntax
        is correct.
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_url(
            "https://used-in-tests.carbontxt.org/carbon-txt-with-csrd-no-renewables-data.txt"
        )

        assert res.result
        assert not res.document_results
        assert not res.exceptions

    def test_validate_file_output_from_svelte_validator(self):
        """
        This should show a failure safely, as the URL is not reachable
        """
        validator = validators.CarbonTxtValidator()

        # this is the expected output from the svelte carbon.txt builder
        svelte_output = pathlib.Path(
            "tests/fixtures/regression.strings-or-lists.carbon.txt.toml"
        )

        path_to_carbon_txt = str(svelte_output.absolute())

        res = validator.validate_url(path_to_carbon_txt)

        assert res.result
        assert not res.exceptions

    def test_validate_with_valid_404_html_page_instead_of_expected_toml(
        self, mocked_404_page_at_carbon_txt_path
    ):
        """
        This should show a failure with the 404 triggering an UnreachableCarbonTxtFile,
        as though we have HTML content being returned in the "not found" response, the
        status code is what we check for first, and it is a 404.
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_url(mocked_404_page_at_carbon_txt_path)

        assert not res.result
        assert res.exceptions
        assert len(res.exceptions) == 1

        assert "UnreachableCarbonTxtFile" in res.exceptions[0]

    def test_validate_with_valid_200_html_instead_of_expected_toml(
        self, mocked_not_found_page_at_carbon_txt_path
    ):
        """
        This should show a failure, as the HTML is not a valid carbon.txt file
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_url(mocked_not_found_page_at_carbon_txt_path)

        assert not res.result
        assert res.exceptions
        assert len(res.exceptions) == 1

        # TODO we list the exception class name in the exception message.
        # Consider providing more structured information to render in the
        # CLI and validator web UI

        assert "NotParseableTOMLButHTML" in res.exceptions[0]
