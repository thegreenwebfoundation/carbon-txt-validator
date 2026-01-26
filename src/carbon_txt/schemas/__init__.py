from datetime import date
from typing import Dict

from .version_0_2 import CarbonTxtFile as CarbonTxtFile0_2
from .version_0_3 import CarbonTxtFile as CarbonTxtFile0_3
from .version_0_4 import CarbonTxtFile as CarbonTxtFile0_4


CarbonTxtFile = CarbonTxtFile0_2 | CarbonTxtFile0_3 | CarbonTxtFile0_4
CarbonTxtFileType = (
    type[CarbonTxtFile0_2] | type[CarbonTxtFile0_3] | type[CarbonTxtFile0_4]
)

VERSIONS: Dict[str, CarbonTxtFileType] = {
    "0.2": CarbonTxtFile0_2,
    "0.3": CarbonTxtFile0_3,
    "0.4": CarbonTxtFile0_4,
}

DEFAULT_VERSION: str = "0.2"

LATEST_VERSION: str = "0.4"


class InvalidVersionError(ValueError):
    def __init__(self, version):
        super().__init__(f"'{version}' is not a valid carbon.txt syntax version")


def build_from_dict(data: dict):
    """
    Helper method to build a carbon.txt syntax tree from a python dictionary describing its contents.
    This method will automatically pick the correct version of the carbon.txt syntax, based on the supplied
    "version" attribute, or default to the latest version if not supplied.
    In addition, it will set the "last_updated" field to the current date if unspecified, and if the specified
    syntax version supports it. This can be omitteed by explicitly setting last_updated to None.
    If the supplied data does not produce a valid CarbonTxt syntax tree, a ValidationError
    """

    # We take a copy of the data dict so we can mutate it
    # below without affecting the value in the calling context
    data = data.copy()

    if "version" not in data:
        data["version"] = LATEST_VERSION

    version = data["version"]

    if version not in VERSIONS.keys():
        raise InvalidVersionError(version)

    FileClass = VERSIONS[version]

    if "last_updated" in FileClass.model_fields and "last_updated" not in data:
        data["last_updated"] = date.today()

    # ModelValidate will build the entire tree of pydantic objects, or raise a ValidationError if the
    # supplied data is invalid.
    return FileClass.model_validate(data)
