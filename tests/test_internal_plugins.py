# import pytest
from carbon_txt import validators  # type: ignore


from structlog import get_logger

logger = get_logger()


class TestCarbonTxtValidatorWithCSRDPlugin:
    def test_validate_carbon_txt_file_with_csrd_report(
        self, settings_with_active_csrd_greenweb_plugin, settings
    ):
        """
        Test that we can validate a carbon.txt file valid CSRD report, and that
        we can extract values from the CSRD report.
        """

        validator = validators.CarbonTxtValidator(
            active_plugins=settings.ACTIVE_CARBON_TXT_PLUGINS
        )

        test_domain = "used-in-tests.carbontxt.org"
        carbon_txt_path = "carbon-txt-with-csrd-and-renewables.txt"
        csrd_report_path = "esrs-e1-efrag-2026-12-31-en.xhtml"

        data_point_codes = [
            "PercentageOfRenewableSourcesInTotalEnergyConsumption",
            "PercentageOfEnergyConsumptionFromNuclearSourcesInTotalEnergyConsumption",
            "EnergyConsumptionRelatedToOwnOperations",
            "EnergyConsumptionFromFossilSources",
            "EnergyConsumptionFromNuclearSources",
            "EnergyConsumptionFromRenewableSources",
            "ConsumptionOfPurchasedOrAcquiredElectricityHeatSteamAndCoolingFromRenewableSources",
            "ConsumptionOfSelfgeneratedNonfuelRenewableEnergy",
        ]

        # TODO: Arelle is very slow when parsing an CSRD report for the first time.
        # look into caching, or making this faster
        res = validator.validate_url(f"https://{test_domain}/{carbon_txt_path}")

        csrd_plugin_parse_results = res.document_results.get("csrd_greenweb")
        csrd_report_url = f"https://{test_domain}/{csrd_report_path}"

        for result in csrd_plugin_parse_results:
            assert result.file == csrd_report_url
            assert result.short_code in data_point_codes

        assert res.result
        assert not res.exceptions
