from typing import Generic

from .common import DocTypeT, Organisation
from .version_0_2 import DisclosureDocType
from .version_0_3 import CarbonTxtFile as CarbonTxtFileV3
from .version_0_3 import Disclosure as DisclosureV3


class Disclosure(DisclosureV3[DocTypeT], Generic[DocTypeT]):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.4 syntax, disclosures have all the same fields as in
    version 0.3, plus an optional title string.
    """

    title: str | None = None

    @property
    def toml_fields(self) -> list[str]:
        return super().toml_fields + ["title"]


class CarbonTxtFile(CarbonTxtFileV3):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.4 syntax, which adds an optional title
    attribute for disclosures.
    """

    org: Organisation[Disclosure[DisclosureDocType]]
