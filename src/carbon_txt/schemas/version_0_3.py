from datetime import date
from typing import Generic

from pydantic import Field

from .common import (
    VERSION_NUMBER_PATTERN,
    DocTypeT,
    Organisation,
    Upstream,
)
from .common import (
    CarbonTxtFile as BaseCarbonTxtFile,
)
from .common import (
    Disclosure as BaseDisclosure,
)
from .version_0_2 import DisclosureDocType


class Disclosure(BaseDisclosure[DocTypeT], Generic[DocTypeT]):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.3 syntax, disclosures have all the same fields as in
    version 0.2, plus an optional valid_until date.
    """

    # __name__ must be overridden so that Pydantic uses the correct type
    # name in the generated JSON schema
    __name__ = "Disclosure"

    valid_until: date | None = None

    @property
    def toml_fields(self) -> list[str]:
        return super().toml_fields + ["valid_until"]


class CarbonTxtFile(BaseCarbonTxtFile):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.3 syntax, which strictly includes the version
    attribute, has an optional last_updated date, and has an optional valid_until
    date for disclosures.
    """

    version: str = Field(pattern=VERSION_NUMBER_PATTERN)
    last_updated: date | None = None
    upstream: Upstream | None = None
    org: Organisation[Disclosure[DisclosureDocType]]

    @property
    def toml_fields(self) -> list[str]:
        return ["version", "last_updated", "org", "upstream"]
