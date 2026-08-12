from typing import Literal

from pydantic import Field

from .common import (
    VERSION_NUMBER_PATTERN,
    Organisation,
    OtherDisclosureDocType,
    Upstream,
)
from .common import (
    CarbonTxtFile as BaseCarbonTxtFile,
)
from .common import (
    Disclosure as BaseDisclosure,
)

SpecificDisclosureDocType = Literal[
    "web-page",
    "annual-report",
    "sustainability-page",
    "certificate",
    "csrd-report",
]


DisclosureDocType = Literal[SpecificDisclosureDocType, OtherDisclosureDocType]

Disclosure = BaseDisclosure[DisclosureDocType]


class CarbonTxtFile(BaseCarbonTxtFile):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.2 syntax, which optionally includes the version
    attribute, has no last_updated date, and does not provide a valid_until date for disclosures.
    """

    version: str | None = Field(pattern=VERSION_NUMBER_PATTERN, default="0.2")
    upstream: Upstream | None = None
    org: Organisation[Disclosure]

    @property
    def toml_fields(self) -> list[str]:
        return ["version", "org", "upstream"]
