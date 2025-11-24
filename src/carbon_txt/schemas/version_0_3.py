from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import Organisation, Upstream, VERSION_NUMBER_PATTERN
from .common import Disclosure as BaseDisclosure


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


class CarbonTxtFile(BaseModel):
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
