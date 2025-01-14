from carbon_txt import validators  # type: ignore
import pytest


class TestCarbonTxtValidator:
    def test_validate_file_with_greenweb_root(self):
        """
        This should show a failure, as thegreenwebfoundation.org does not currently have a carbon.txt file,
        but does serve content at the root path (i.e. '/')
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_url("https://www.thegreenwebfoundation.org")
        assert not res.result
        assert res.exceptions

    def test_validate_file_with_greenweb_carbon_txt(self):
        """
        This should show a failure, as thegreenwebfoundation.org does not currently have a carbon.txt file
        """
        validator = validators.CarbonTxtValidator()
        res = validator.validate_url("https://www.thegreenwebfoundation.org/carbon.txt")
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
