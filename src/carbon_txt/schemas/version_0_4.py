from typing import Optional

from .common import Organisation
from .version_0_3 import CarbonTxtFile as CarbonTxtFileV3, Disclosure as DisclosureV3


class Disclosure(DisclosureV3):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.4 syntax, disclosures have all the same fields as in
    version 0.3, plus an optional title string.
    """

    # __name__ must be overridden so that Pydantic uses the correct type
    # name in the generated JSON schema
    __name__ = "Disclosure"

    title: Optional[str] = None


class CarbonTxtFile(CarbonTxtFileV3):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.4 syntax, which adds an optional title
    attribute for disclosures.
    """

    org: Organisation[Disclosure]
