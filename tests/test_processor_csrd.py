import pathlib

import pytest
from arelle import (  # type: ignore
    ModelXbrl,
)
from structlog import get_logger

from carbon_txt import processors  # type: ignore

logger = get_logger()


@pytest.fixture
def local_esrs_1_csrd_file():
    file_path = (
        pathlib.Path(__file__).parent / "fixtures" / "esrs-e1-efrag-2026-12-31-en.xhtml"
    )
    return str(file_path)


@pytest.fixture
def local_esrs_2_csrd_file():
    """A file with no values for renewable energy percentage"""
    file_path = (
        pathlib.Path(__file__).parent
        / "fixtures"
        / "esrs-e2-efrag-2026-12-31-en-no-renewables.xhtml"
    )
    return str(file_path)


class TestCSRDProcessorValidate:  # noqa
    def test_basic_fetch_of_CSRD_reports(self, local_esrs_1_csrd_file):
        """
        Test that we can fetch a remote CSRD report, and that it is not empty.
        """

        arelle_wrapper = processors.ArelleProcessor(local_esrs_1_csrd_file)
        res = arelle_wrapper.parsed_reports()

        assert res
        assert isinstance(res[0], ModelXbrl.ModelXbrl)
        assert len(res) > 0

    def test_basic_validation_of_CSRD_report(self, local_esrs_1_csrd_file):
        """
        Test that we can parse a remote CSRD report, and pull out values for specific datapoints.
        """
        short_code = "PercentageOfRenewableSourcesInTotalEnergyConsumption"

        csrd_processor = processors.GreenwebCSRDProcessor(
            report_url=local_esrs_1_csrd_file
        )

        res = csrd_processor.get_esrs_datapoint_values([short_code])

        assert len(res) is not None
        for datapoint in res:
            assert (
                datapoint.name
                == "Percentage of renewable sources in total energy consumption"
            )
            assert datapoint.short_code == short_code
            assert datapoint.value > 0.2
            assert datapoint.value < 0.3

    def test_basic_validation_of_CSRD_report_no_value(self, local_esrs_2_csrd_file):
        """
        Test that we get a graceful failure when we try to pull datapoints
        from a report without the values
        """
        csrd_processor = processors.GreenwebCSRDProcessor(
            report_url=local_esrs_1_csrd_file,
        )
        datapoint_code = "PercentageOfRenewableSourcesInTotalEnergyConsumption"

        res = csrd_processor.get_esrs_datapoint_values([datapoint_code])
        for item in res:
            assert isinstance(item, processors.NoMatchingDatapointsError)

    def test_safe_error_when_CSRD_unparsable(self):
        """
        Test that we get a graceful failure when we try to parse a unreachable or unparseable
        CSRD report.
        """

        with pytest.raises(processors.NoLoadableCSRDFile):
            processors.ArelleProcessor("https://www.example.com/no-csrd-report")

    def test_basic_validation_of_multiple_values_in_CSRD_report(
        self, local_esrs_1_csrd_file
    ):
        """
        Test that we can parse a remote CSRD report, and pull out values for specific datapoints.
        """

        csrd_processor = processors.GreenwebCSRDProcessor(
            report_url=local_esrs_1_csrd_file
        )

        short_codes = [
            "PercentageOfRenewableSourcesInTotalEnergyConsumption",
            "ConsumptionOfPurchasedOrAcquiredElectricityHeatSteamAndCoolingFromRenewableSources",
        ]

        res = csrd_processor.get_esrs_datapoint_values(
            csrd_processor.local_datapoint_codes
        )

        assert len(res) is not None

        first_renewables_percentage, *rest = [
            datapoint for datapoint in res if datapoint.short_code == short_codes[0]
        ]
        first_renewables_consumption, *rest = [
            datapoint for datapoint in res if datapoint.short_code == short_codes[1]
        ]

        assert (
            first_renewables_percentage.name
            == "Percentage of renewable sources in total energy consumption"
        )
        assert first_renewables_percentage.short_code == short_codes[0]
        assert first_renewables_percentage.value > 0.2
        assert first_renewables_percentage.value < 0.3

        assert (
            first_renewables_consumption.name
            == "Consumption of purchased or acquired electricity, heat, steam, and cooling from renewable sources"
        )
        assert first_renewables_consumption.short_code == short_codes[1]
        assert first_renewables_consumption.value == "450000"


@pytest.mark.skip(
    "Skipped in CI, as we only use it to check local EFRAG example reports in bulk"
)  # type: ignore
class TestGreenwebCSRDProcessorEFRAGValidateAll:
    """ """

    def test_all_efrag_docs(self):
        data_dir = pathlib.Path(__file__).parent.parent / "data" / "Set1" / "InlineXBRL"
        xhtml_files = list(data_dir.rglob("*.xhtml"))

        good_files = []
        bad_files = []

        for file in xhtml_files:
            try:
                processor = processors.GreenwebCSRDProcessor(report_url=str(file))
                res = processor.get_esrs_datapoint_values(
                    ["PercentageOfRenewableSourcesInTotalEnergyConsumption"]
                )
                assert res
                good_files.append(file)
            except ValueError as ex:
                logger.warning(f"Error processing {file}")
                logger.warning(f"Error was {ex}")
                bad_files.append(file)

        logger.info(
            f"We have {len(good_files)} good files, and {len(bad_files)} bad files"
        )
        logger.info("Good files:")
        logger.info(good_files)
        logger.info("Bad files:")
        logger.info(bad_files)
