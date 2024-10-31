from typing import Literal, Optional, List

from pydantic import BaseModel, Field


class Provider(BaseModel):
    """
    Providers in this context are upstream providers of hosted services.
    The domain is used as key for looking up a corresponding provider in the
    Green Web Platform
    """

    domain: str
    name: Optional[str] = None
    services: Optional[List[str]] = None


class Credential(BaseModel):
    """
    Credentials are essentially supporting documentation for a claim to be running on
    green energy.
    """

    domain: Optional[str] = None
    doctype: Literal[
        "web-page", "annual-report", "sustainability-page", "certificate", "other"
    ]
    url: str


class Organisation(BaseModel):
    """
    An Organisation is the entity making the claim to running its infrastructure
    on green energy. In the very least it should have some credentials point to, even
    if it is exclusively relying on upstream providers for its green claims.
    """

    credentials: List[Credential] = Field(..., min_length=1)


class Upstream(BaseModel):
    """
    Upstream refers to one or more providers of hosted services that the Organisation
    is relying on to operate a digital service, like running a website, or application.
    """

    # organisations that don't use third party providers could plausibly have an
    # empty upstream list. We also either accept providers as a single string representing
    # a domain, or a dictionary containing the fields defined in the Provider model
    providers: Optional[List[Provider | str]] = None


class CarbonTxtFile(BaseModel):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    """

    upstream: Optional[Upstream] = None
    org: Organisation
