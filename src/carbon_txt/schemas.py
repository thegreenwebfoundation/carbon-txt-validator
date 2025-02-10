from typing import Literal, Optional, List

from pydantic import BaseModel, Field


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


class Disclosure(BaseModel):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
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


class Organisation(BaseModel):
    """
    An Organisation is the entity making the claim to running its infrastructure
    on green energy. In the very least it should have some disclosures point to, even
    if it is exclusively relying on services from upstream providers for its green claims.
    """

    disclosures: List[Disclosure] = Field(..., min_length=1)


class Upstream(BaseModel):
    """
    Upstream refers to one or more hosted services that the Organisation
    is relying on to operate a digital service, like running a website, or application.
    """

    # organisations that don't use third party providers could plausibly have an
    # empty upstream list. We also either accept providers as a single string representing
    # a domain, or a dictionary containing the fields defined in the Provider model
    services: Optional[List[Service | str]] = None


class CarbonTxtFile(BaseModel):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    """

    upstream: Optional[Upstream] = None
    org: Organisation
