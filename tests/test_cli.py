import json

from typer.testing import CliRunner

from carbon_txt.cli import app

runner = CliRunner(mix_stderr=False)


class TestCLI:
    """
    Test our CLI commands RETURN WHT WE
    """

    def test_lookup_domain(self):
        """
        Run our CLI to `carbontxt validate domain some-domain.com`, and confirm we
        get back the expected URI, and whether the file was valid.
        """

        result = runner.invoke(
            app, ["validate", "domain", "used-in-tests.carbontxt.org"]
        )
        assert result.exit_code == 0
        assert "used-in-tests.carbontxt.org" in result.stdout

    def test_lookup_file(self):
        """
        Run our CLI to `carbontxt validate file https://some-domain.com/carbon.txt`,
        and confirm we end up with the expected URI, and whether the file was valid.
        """

        result = runner.invoke(
            app, ["validate", "file", "https://used-in-tests.carbontxt.org/carbon.txt"]
        )
        assert result.exit_code == 0
        assert "https://used-in-tests.carbontxt.org" in result.stdout

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
