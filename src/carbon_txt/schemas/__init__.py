from typing import Dict

from .version_0_2 import CarbonTxtFile as CarbonTxtFile0_2
from .version_0_3 import CarbonTxtFile as CarbonTxtFile0_3


CarbonTxtFile = CarbonTxtFile0_2 | CarbonTxtFile0_3
CarbonTxtFileType = type[CarbonTxtFile0_2] | type[CarbonTxtFile0_3]

VERSIONS: Dict[str, CarbonTxtFileType] = {
    "0.2": CarbonTxtFile0_2,
    "0.3": CarbonTxtFile0_3,
}

DEFAULT_VERSION: str = "0.2"

LATEST_VERSION: str = "0.3"
