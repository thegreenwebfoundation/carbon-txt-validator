from datetime import date
from typing import Optional, List

from pydantic import ConfigDict, Field

from .common import (
    CarbonTxtFile as BaseCarbonTxtFile,
    Disclosure as BaseDisclosure,
    Organisation,
    Upstream,
    VERSION_NUMBER_PATTERN,
)


class Disclosure(BaseDisclosure):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.3 syntax, disclosures have all the same fields as in
    version 0.2, plus an optional valid_until date.
    """

    # __name__ must be overridden so that Pydantic uses the correct type
    # name in the generated JSON schema
    __name__ = "Disclosure"

    model_config = ConfigDict(extra="forbid")

    valid_until: Optional[date] = None

    @property
    def toml_fields(self) -> List[str]:
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

    model_config = ConfigDict(extra="forbid")

    version: str = Field(pattern=VERSION_NUMBER_PATTERN)
    last_updated: Optional[date] = None
    upstream: Optional[Upstream] = None
    org: Organisation[Disclosure]

    @property
    def toml_fields(self) -> List[str]:
        return ["version", "last_updated", "org", "upstream"]
