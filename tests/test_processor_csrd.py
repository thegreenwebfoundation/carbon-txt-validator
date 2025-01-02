import pytest
import logging
import pathlib
from carbon_txt import processors  # type: ignore

from rich.logging import RichHandler

from arelle import (  # type: ignore
    ModelXbrl,
)

logger = logging.getLogger(__name__)
logger.addHandler(RichHandler())
# logger.setLevel(logging.INFO)


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

        processor = processors.CSRDProcessor(local_esrs_1_csrd_file)
        res = processor.parsed_reports()

        assert res
        assert isinstance(res[0], ModelXbrl.ModelXbrl)
        assert len(res) > 0

    def test_basic_validation_of_CSRD_report(self, local_esrs_1_csrd_file):
        """
        Test that we can parse a remote CSRD report, and pull out values for specific datapoints.
        """

        processor = processors.CSRDProcessor(local_esrs_1_csrd_file)
        res = processor.get_esrs_datapoint_values(
            ["PercentageOfRenewableSourcesInTotalEnergyConsumption"]
        )

        assert len(res) is not None
        for datapoint in res["PercentageOfRenewableSourcesInTotalEnergyConsumption"]:
            assert (
                datapoint.name
                == "Percentage of renewable sources in total energy consumption"
            )
            assert datapoint.value > 0.2
            assert datapoint.value < 0.3

    def test_basic_validation_of_CSRD_report_no_value(self, local_esrs_2_csrd_file):
        """
        Test that we get a graceful failure when we try to pull datapoints
        from a report without the values
        """

        processor = processors.CSRDProcessor(local_esrs_2_csrd_file)
        datapoint_code = "PercentageOfRenewableSourcesInTotalEnergyConsumption"

        res = processor.get_esrs_datapoint_values([datapoint_code])
        for item in res[datapoint_code]:
            assert isinstance(item, processors.NoMatchingDatapointsError)


@pytest.mark.skip(
    "Skipped in CI, as we only use it to check local EFRAG example reports in bulk"
)  # type: ignore
class TestCSRDProcessorEFRAGValidateAll:
    """ """

    def test_all_efrag_docs(self):
        data_dir = pathlib.Path(__file__).parent.parent / "data" / "Set1" / "InlineXBRL"
        xhtml_files = list(data_dir.rglob("*.xhtml"))

        good_files = []
        bad_files = []

        for file in xhtml_files:
            try:
                processor = processors.CSRDProcessor(str(file))
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
