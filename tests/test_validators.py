from carbon_txt import validators  # type: ignore

validator = validators.CarbonTxtValidator()


class TestCarbonTxtValidator:
    def test_validate_file_with_greenweb_root(self):
        """
        This should show a failure, as thegreenwebfoundation.org does not currently have a carbon.txt file,
        but does serve content at the root path (i.e. '/')
        """
        res = validator.validate_url("https://www.thegreenwebfoundation.org")
        assert not res.result

    def test_validate_file_with_greenweb_carbon_txt(self):
        """
        This should show a failure, as thegreenwebfoundation.org does not currently have a carbon.txt file
        """
        res = validator.validate_url("https://www.thegreenwebfoundation.org/carbon.txt")
        assert not res.result
