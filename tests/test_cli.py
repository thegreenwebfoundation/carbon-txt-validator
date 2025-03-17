import json

from typer.testing import CliRunner

from carbon_txt.cli import app  # type: ignore

runner = CliRunner(mix_stderr=False)


class TestCLI:
    """
    Test our CLI commands RETURN WHT WE
    """

    def test_lookup_domain(self, mocked_carbon_txt_domain):
        """
        Run our CLI to `carbontxt validate domain some-domain.com`, and confirm we
        get back the expected URI, and whether the file was valid.
        """

        result = runner.invoke(app, ["validate", "domain", mocked_carbon_txt_domain])
        assert result.exit_code == 0
        assert "used-in-tests.carbontxt.org" in result.stdout

    def test_lookup_file(self, mocked_carbon_txt_url):
        """
        Run our CLI to `carbontxt validate file https://some-domain.com/carbon.txt`,
        and confirm we end up with the expected URI, and whether the file was valid.
        """

        result = runner.invoke(app, ["validate", "file", mocked_carbon_txt_url])

        assert result.exit_code == 0
        assert "https://used-in-tests.carbontxt.org" in result.stdout

    def test_lookup_missing_file(self):
        """
        Run our CLI to `carbontxt validate file https://some-domain.com/carbon.txt`,
        """

        # TODO: Update to a domain we know will not ever have a carbon.txt file
        result = runner.invoke(
            app, ["validate", "file", "https://www.thegreenwebfoundation.org"]
        )

        assert result.exit_code == 1

    def test_schema(self):
        """
        Run our CLI to `carbontxt schema`, and confirm we
        get back the expected JSON Schema representation of our domain objects
        """

        result = runner.invoke(app, ["schema"])
        parsed_schema = json.loads(result.stdout)

        assert result.exit_code == 0
        assert "JSON Schema for a carbon.txt file" in result.stderr
        assert "CarbonTxtFile" in parsed_schema.get("title")
        assert "$defs" in parsed_schema.keys()

    def test_lookup_domain_with_test_plugin(self, mocked_carbon_txt_domain):
        """
        Test that we can run the CLI with a custom plugin directory
        """

        result = runner.invoke(
            app,
            [
                "validate",
                "domain",
                mocked_carbon_txt_domain,
                "--plugins-dir",
                "tests/test_plugins",
            ],
        )
        assert result.exit_code == 0
        assert "used-in-tests.carbontxt.org" in result.stdout

        # check that we see output from the test plugin
        assert "Test Plugin:" in result.stdout
