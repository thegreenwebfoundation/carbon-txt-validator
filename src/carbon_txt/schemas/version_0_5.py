from typing import Literal

from .common import (
    Organisation,
    SpecificDisclosureDocType as SpecificDisclosureDocTypeV4,
    OtherDisclosureDocType,
)
from .version_0_4 import CarbonTxtFile as CarbonTxtFileV4, Disclosure as DisclosureV4


type SpecificDisclosureDocType = Literal[SpecificDisclosureDocTypeV4, "ai-model-card"]


class Disclosure(DisclosureV4):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.4 syntax, disclosures have all the same fields as in
    version 0.3, plus an optional title string.
    """

    # __name__ must be overridden so that Pydantic uses the correct type
    # name in the generated JSON schema
    __name__ = "Disclosure"

    doc_type: Literal[SpecificDisclosureDocType, OtherDisclosureDocType]


class CarbonTxtFile(CarbonTxtFileV4):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.4 syntax, which adds an optional title
    attribute for disclosures.
    """

    org: Organisation[Disclosure]
