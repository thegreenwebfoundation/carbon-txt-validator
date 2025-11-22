from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import Disclosure, Organisation, Upstream, VERSION_NUMBER_PATTERN


class CarbonTxtFile(BaseModel):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.2 syntax, which optionally includes the version
    attribute, has no last_updated date, and does not provide a valid_until date for disclosures.
    """

    model_config = ConfigDict(extra="forbid")

    version: Optional[str] = Field(pattern=VERSION_NUMBER_PATTERN, default="0.2")
    upstream: Optional[Upstream] = None
    org: Organisation[Disclosure]
