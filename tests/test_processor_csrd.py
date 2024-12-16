import pytest  # noqa

import pathlib
from carbon_txt import processors


@pytest.fixture
def local_esrs_1_csrd_file():
    file_path = (
        pathlib.Path(__file__).parent / "fixtures" / "esrs-e1-efrag-2026-12-31-en.xbrl"
    )
    return str(file_path)


class TestCSRDProcessorValidate:
    def test_basic_validation_of_CSRD_report(self, local_esrs_1_csrd_file):
        """
        Test that we can parse a remote CSRD report, and pull out the values for a specific datapoint.
        """

        processor = processors.CSRDProcessor(local_esrs_1_csrd_file)
        res = processor.get_esrs_datapoint_values(
            "PercentageOfRenewableSourcesInTotalEnergyConsumption"
        )

        assert len(res) is not None
        for val in res:
            assert val.isNumeric
            assert float(val.effectiveValue) > 0.2
            assert float(val.effectiveValue) < 0.3
