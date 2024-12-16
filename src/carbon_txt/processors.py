from arelle import ModelXbrl
from arelle.api.Session import Session
from arelle.RuntimeOptions import RuntimeOptions
from arelle import ModelInstanceObject

# model_xbrl = model_xbrls[0]
# model_xbrl.factsByQname

# this file is the same one as in this gist
# https://gist.github.com/mrchrisadams/fb14e79d2d52977255c0b1db6de86726


class CSRDProcessor:
    """
    A processor for reading and parsing CSRD report documents.
    """

    xbrls: list[ModelXbrl.ModelXbrl]

    esrs_datapoints: list[str] = [
        "PercentageOfRenewableSourcesInTotalEnergyConsumption",
    ]

    def __init__(self, report_url: str) -> None:
        """
        Initialize the Processor loading the report from the given URL.
        """

        options = RuntimeOptions(
            entrypointFile=str(report_url),
            # we need to keep the file open to fetch data from the xml
            # file later, when we call various method on the object
            # TODO: does file close when this object is garbage collected?
            keepOpen=True,
        )

        with Session() as session:
            session.run(options)
            self.xbrls = session.get_models()

    def parsed_reports(self) -> list[ModelXbrl.ModelXbrl]:
        """
        Read a CSRD report from a URL, and return the parsed report as a an object
        """
        return self.xbrls

    def get_esrs_datapoint_values(
        self, datapoint_code: str
    ) -> list[ModelInstanceObject.ModelFact]:
        try:
            res = self.xbrls[0].factsByLocalName.get(datapoint_code)
            return [*res]
        except KeyError:
            raise ValueError(f"Could not find datapoint with code {datapoint_code}")
