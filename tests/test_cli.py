from typer.testing import CliRunner

from carbon_txt.cli import app

runner = CliRunner()


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
