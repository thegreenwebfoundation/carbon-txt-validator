from datetime import date
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field


# Modified semver regex, taken from
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string,
# adapted to make the patch version optional, so it will accept eg 0.2, 0.3.
VERSION_NUMBER_PATTERN = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)(?:\.(?P<patch>0|[1-9]\d*))?(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


class Service(BaseModel):
    """
    A service in this context is a hosted service, offered by a provider
    of hosted services.
    The domain is used as key for looking up a corresponding provider in the
    Green Web Platform
    """

    domain: Optional[str]
    name: Optional[str] = None
    # TODO: python prefers snake_case.
    # javascript prefers camelCase
    # but kebab-case is arguable more common in URLS
    # how do we support this?
    service_type: Optional[List[str]] | str = None


class Disclosure0_2(BaseModel):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.2 syntax, disclosures do not have a valid_until date.
    """

    domain: Optional[str] = None
    doc_type: Literal[
        "web-page",
        "annual-report",
        "sustainability-page",
        "certificate",
        "csrd-report",
        "other",
    ]
    url: str


class Disclosure0_3(Disclosure0_2):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.3 syntax, disclosures have all the same fields as in
    version 0.2, plus an optional valid_until date.
    """

    valid_until: Optional[date] = None


class Organisation[DisclosureType](BaseModel):
    """
    An Organisation is the entity making the claim to running its infrastructure
    on green energy. In the very least it should have some disclosures point to, even
    if it is exclusively relying on services from upstream providers for its green claims.
    """

    disclosures: List[DisclosureType] = Field(..., min_length=1)


class Upstream(BaseModel):
    """
    Upstream refers to one or more hosted services that the Organisation
    is relying on to operate a digital service, like running a website, or application.
    """

    # organisations that don't use third party providers could plausibly have an
    # empty upstream list. We also either accept providers as a single string representing
    # a domain, or a dictionary containing the fields defined in the Provider model
    services: Optional[List[Service | str]] = None


class CarbonTxtFile0_2(BaseModel):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.2 syntax, which optionally includes the version
    attribute, has no last_updated date, and does not provide a valid_until date for disclosures.
    """

    version: Optional[str] = Field(pattern=VERSION_NUMBER_PATTERN, default="0.2")
    upstream: Optional[Upstream] = None
    org: Organisation[Disclosure0_2]


class CarbonTxtFile0_3(BaseModel):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.3 syntax, which strictly includes the version
    attribute, has an optional last_updated date, and has an optional valid_until
    date for disclosures.
    """

    version: str = Field(pattern=VERSION_NUMBER_PATTERN)
    last_updated: Optional[date] = None
    upstream: Optional[Upstream] = None
    org: Organisation[Disclosure0_3]


CarbonTxtFile = CarbonTxtFile0_2 | CarbonTxtFile0_3
CarbonTxtFileType = type[CarbonTxtFile0_2] | type[CarbonTxtFile0_3]

VERSIONS: Dict[str, CarbonTxtFileType] = {
    "0.2": CarbonTxtFile0_2,
    "0.3": CarbonTxtFile0_3,
}

DEFAULT_VERSION: str = "0.2"

LATEST_VERSION: str = "0.3"
