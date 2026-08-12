from typing import Generic, Literal, TypeAlias

from .common import DocTypeT, Organisation, OtherDisclosureDocType

from .version_0_2 import (
    SpecificDisclosureDocType as SpecificDisclosureDocTypeV2,
)
from .version_0_4 import CarbonTxtFile as CarbonTxtFileV4, Disclosure as DisclosureV4


SpecificDisclosureDocType: TypeAlias = Literal[
    SpecificDisclosureDocTypeV2, "ai-model-card", OtherDisclosureDocType
]

DisclosureDocType: TypeAlias = Literal[
    SpecificDisclosureDocType, OtherDisclosureDocType
]


class Disclosure(DisclosureV4, Generic[DocTypeT]):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.5 syntax, we add a new document type, 'ai-model-card'
    to the enumeration of possible document types.
    """

    # __name__ must be overridden so that Pydantic uses the correct type
    # name in the generated JSON schema
    __name__ = "Disclosure"


class CarbonTxtFile(CarbonTxtFileV4):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.5 syntax, which the 'ai-model-card' document type.
    """

    org: Organisation[Disclosure[DisclosureDocType]]
