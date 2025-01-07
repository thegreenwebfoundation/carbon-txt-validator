import pytest
from django.conf import settings

from carbon_txt import validators  # type: ignore


@pytest.fixture()
def settings_with_active_csrd_plugin_(settings):
    settings.ACTIVE_CARBON_TXT_PLUGINS = ("carbon_txt.process_csrd_document",)


class TestCarbonTxtValidatorWithCSRDPlugin:
    def test_validate_carbon_txt_file_with_csrd_report(
        self, settings_with_active_csrd_plugin_
    ):
        """
        Test that we can validate a carbon.txt file valid CSRD report, and that
        we can extract values from the CSRD report.
        """

        validator = validators.CarbonTxtValidator(
            active_plugins=settings.ACTIVE_CARBON_TXT_PLUGINS
        )

        # TODO: Arelle is very slow when parsing an CSRD report for the first time.
        # look into caching, or making this faster
        res = validator.validate_url(
            "https://used-in-tests.carbontxt.org/carbon-txt-with-csrd-and-renewables.txt"
        )

        csrd_plugin_parse_results = res.document_results[0]
        csrd_report_url = (
            "https://used-in-tests.carbontxt.org/esrs-e1-efrag-2026-12-31-en.xhtml"
        )
        for key in [
            "PercentageOfRenewableSourcesInTotalEnergyConsumption",
            "PercentageOfEnergyConsumptionFromNuclearSourcesInTotalEnergyConsumption",
            "EnergyConsumptionRelatedToOwnOperations",
            "EnergyConsumptionFromFossilSources",
            "EnergyConsumptionFromNuclearSources",
            "EnergyConsumptionFromRenewableSources",
            "ConsumptionOfPurchasedOrAcquiredElectricityHeatSteamAndCoolingFromRenewableSources",
            "ConsumptionOfSelfgeneratedNonfuelRenewableEnergy",
        ]:
            assert key in csrd_plugin_parse_results[csrd_report_url].keys()

        assert res.result
        assert not res.exceptions
