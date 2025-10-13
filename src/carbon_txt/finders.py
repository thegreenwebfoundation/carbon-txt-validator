from dataclasses import dataclass
import pathlib
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import ParseResult, urlparse
import importlib.metadata
import re
import traceback

import tldextract
import dns.resolver
import httpx
import rich  # noqa
from .exceptions import UnreachableCarbonTxtFile

from . import parsers_toml

from structlog import get_logger

import logging

logger = get_logger()


parser = parsers_toml.CarbonTxtParser()

DelegationMethod = Optional[Literal["http", "dns"]]


@dataclass
class FinderResult:
    """
    Encapsulates the result of succesfully looking up the location of a carbon.txt for a domain, which
    doesn't just include the uri of the carbon.txt itself, but also the method by which it was found.
    """

    uri: str
    delegation_method: DelegationMethod = None


def log_safely(log_message: str, logs: Optional[list], level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs:
        logs.append(log_message)


class FileFinder:
    """
    Responsible for figuring out which URI to fetch
    a carbon.txt file from.
    """

    def __init__(
        self, http_timeout: float = 5.0, http_user_agent: Optional[str] = None
    ):
        self.http_timeout = http_timeout

        if http_user_agent is not None:
            self.http_user_agent = http_user_agent
        else:
            version = importlib.metadata.version("carbon_txt")
            self.http_user_agent = (
                f"CarbonTxtValidator/{version} (https://carbontxt.org/tools/validator)"
            )

    def update_tld_suffix_list(self) -> None:
        """
        Updates the  public suffix list used by tldextract.
        This is used to identify whether a domain is a TLD or not
        when resolving carbon.txt locations
        """
        tldextract.update(fetch_now=True)



    def _parse_uri(self, uri: str) -> Optional[ParseResult]:
        """
        Return a parsed URI object if the URI is valid, otherwise return None
        """
        parsed_uri = urlparse(uri)

        if parsed_uri.scheme in ("http", "https"):
            return parsed_uri

        return None

    @property
    def http_headers(self) -> dict[str, str]:
        return {"User-Agent": self.http_user_agent}

    def _lookup_dns(self, domain: str) -> Optional[str]:
        """
        Try a DNS TXT record lookup for the given domain,
        returning the delegated carbon.txt URI if found
        """

        # look for a TXT record on the domain first
        # if there is a valid TXT record on it, return that
        try:
            answers = dns.resolver.resolve(domain, "TXT")

            for answer in answers:
                txt_record = answer.to_text().strip('"')
                if txt_record.startswith("carbon-txt-location"):
                    # pull out our URL to check
                    _, override_url = txt_record.split("=")

                    if override_url is not None:
                        logger.info(
                            f"Found an override_url to use from the DNS lookup: {override_url}"
                        )
                        return override_url

        except dns.resolver.NoAnswer:
            logger.info("No result from TXT lookup")
            return None
        except dns.resolver.NXDOMAIN as ex:
            logger.info(f"No result from TXT lookup: {ex.msg}")
            return None
        except Exception as ex:
            logger.exception(f"New exception: {ex}")
            return None

        return None

    def _is_tld(self, domain : str) -> bool:
        """
        Tests if a given domain is a TLD
        """
        tld = tldextract.extract(domain).top_domain_under_public_suffix
        return domain == tld

    def _is_www_subdomain(self, domain : str) -> bool:
        """
        Tests if a given domain is a www subdomain of a TLD
        """
        tld = tldextract.extract(domain).top_domain_under_public_suffix
        return domain == f"www.{tld}"

    def _alternate_domain(self, domain : str) -> Optional[str]:
        """
        Returns the "alternate" variant for a domain, for which resolution should be attempted if no method succeeds for the original domain.
         . For TLDS, this is the www. subdomain,
         - For www subdomains, this is the TLD,
         - For all other domain names, no alternate is defined.
        """
        if self._is_tld(domain):
            return f"www.{domain}"
        elif self._is_www_subdomain(domain):
            return re.sub("^www\\.", "", domain)
        else:
            return None

    def _check_for_hosted_carbon_txt(self, url, logs=None) -> Optional[str]:
        """
        Check for a hosted carbon.txt file at the given URL, and returns the URL if present
        """
        message = f"Checking if a carbon.txt file is reachable at {url}"
        log_safely(message, logs)
        uri = urlparse(url)
        try:
            response = self.resolve_uri(uri.geturl(), logs)
            if response:
                log_safely(f"New Carbon text file found at: {response.uri}", logs)
                return response.uri
        except UnreachableCarbonTxtFile:
            pass

    def _check_for_dns_delegation(self, domain: str, logs=None) -> Optional[str]:
        """
        Check for a 'carbon-txt-location' DNS TXT record, and return the URL in the record if present
        """
        log_safely(f"Trying a DNS delegated lookup for domain {domain}", logs)
        if uri_from_domain := self._lookup_dns(domain):
            log_safely(f"New lookup found for domain {domain}: {uri_from_domain}", logs)
            return self.resolve_domain_or_uri(uri_from_domain, logs).uri

    def _check_for_http_header_delegation(
        self, domain: str, logs=None
    ) -> Optional[str]:
        """
        Check for a 'CarbonTxt-Location' header in the response, and return the URL in the header if present
        """
        log_safely(
            f"Checking for a 'CarbonTxt-Location' header in the response: http://{domain}",
            logs,
        )
        response = httpx.head(
            f"https://{domain}", timeout=self.http_timeout, headers=self.http_headers
        )
        if "carbontxt-location" in response.headers:
            header_url = response.headers.get("carbontxt-location")
            if header_url is not None:
                log_safely(
                    f"Found a 'CarbonTxt-Location' header, following to {header_url}",
                    logs,
                )
                try:
                    parsed_url = str(httpx.URL(header_url))
                    return self.resolve_domain_or_uri(parsed_url, logs).uri
                except httpx.InvalidURL:
                    logger.error(
                        f"Invalid URL in 'CarbonTxt-Location' header: {header_url}"
                    )

    def fetch_carbon_txt_file(self, uri: str, logs=None) -> str:
        """
        Accept a URI and either fetch the file over HTTP(S), or read the local file.
        Return a string of contents of the remote carbon.txt file, or the local file.
        """
        if uri.startswith("http"):
            try:
                response = httpx.get(
                    uri, timeout=self.http_timeout, headers=self.http_headers
                )
                response.raise_for_status()
                result = response.text
                return result
            except httpx.ConnectError as ex:
                raise UnreachableCarbonTxtFile(
                    f"Could not connect to {uri}. Error was: {ex}"
                )
            except httpx.HTTPStatusError as exc:
                raise UnreachableCarbonTxtFile(
                    f"Requesting {uri} returned an HTTP {exc.response.status_code} response"
                )

        if pathlib.Path(uri).exists():
            return pathlib.Path(uri).read_text()

        raise ValueError(f"Could not fetch file contents at {str}")

    def resolve_domain_or_uri(self, domain_or_uri: str, logs=None) -> FinderResult:
        """
        Accepts EITHER an HTTP or HTTP URI, OR a Fully-qualified domain name.
        In the case where an HTTP(S) URI is provided, it is taken to refer to
        the location of a carbon.txt file, and no further delegation resolution
        is attempted. In the case of a FQDN, we follow the domain delegation logic,
        checking for carbon.txt in the root and .well-known locations, and then for
        a carbon-txt-location DNS TXT record or a Carbon-Txt-Location HTTP header.
        """
        if domain_or_uri.startswith("http"):
            return self.resolve_uri(domain_or_uri, logs)
        else:
            return self.resolve_domain(domain_or_uri, logs)

    def resolve_domain(
        self, domain: str, logs: Optional[list] = None, checking_alternate: bool = False
    ) -> FinderResult:
        """
        Accepts a domain, and returns a URI to fetch a carbon.txt file from.

        Follows delegation logic from DNS TXT records, and the 'CarbonTxt-Location' header in
        HTTP responses to resolve to a final URL for a carbon.txt file, in the following order of priority.

        - delegation with DNS record
        - carbon.txt file at /carbon.txt
        - carbon.txt file at .well-known/carbon.txt
        - delegation with HTTP header

        This method is called recursively if the DNS TXT record or CarbonTxt-Location Header are present
        and also point to a domain rather than a full carbon.txt URL. If the header or TXT record points to
        a full path to a file, no further delegation is attempted.


        In the case that a www. subdomain or TLD is looked up, the alternative variant is attempted too, if and only
        if no carbon.txt is found at the original domain requested. All other subdomains are treated normally and no
        alternative domain is tried.
        """
        try:
            # First, we check whether a carbon-txt-location DNS TXT record exists
            if candidate := self._check_for_dns_delegation(domain, logs):
                return FinderResult(candidate, "dns")

        # If no DNS record exists, we look for a carbon.txt file at
        # the root of the domain. If that isn't there try a fallback
        # to one at the `.well-known` path:
            default_paths = ["/carbon.txt", "/.well-known/carbon.txt"]

            for url_path in default_paths:
                if candidate := self._check_for_hosted_carbon_txt(
                    f"https://{domain}{url_path}", logs
                ):
                    return FinderResult(candidate, None)

            # If we have not found a carbon.txt file at the root or in the
            # .well-known directory, check for a CarbonTxt-Location HTTP header:
            if candidate := self._check_for_http_header_delegation(domain, logs):
                return FinderResult(candidate, "http")
        except Exception as e:
            # If an exception occurs, we still want to continue to test alternate domains, and ultimately
            # raise an UnreachableCarbonTxtFile exception. However, we log the underlying error for
            # tracability.

            message = traceback.format_exception(e)
            log_safely(f"Encountered an exception while attempting to resolve requested domain:\n{message}", logs)

        #If all of the above fail, we check for an "alternate domain", if there is any:
        alternate_domain = self._alternate_domain(domain)
        if not checking_alternate and alternate_domain:
            log_safely(f"Requested domain has a permitted alternate: {alternate_domain}. Falling back to check", logs)
            try:
                return self.resolve_domain(alternate_domain, logs, checking_alternate=True)
            except UnreachableCarbonTxtFile:
                # We want to raise the error for the actual domain requested, not the alternate.
                pass

        # If none of the above yield a reachable carbon.txt file, raise an error.
        raise UnreachableCarbonTxtFile(
            f"Unable to find a valid carbon.txt file at the domain {domain}"
        )

    def resolve_uri(self, uri: str, logs=None) -> FinderResult:
        """
        Accept a URI pointing to a carbon.txt file, and return the final
        resolved URI, without following any 'CarbonTxt-Location' referrers or similar.

        This does NOT try to fetch the file, just resolve the final URI to fetch it from and
        check that it is reachable.
        """

        # check if the URI looks like one we might reach over HTTP / HTTPS
        parsed_uri = self._parse_uri(uri)

        # if there is no HTTP or HTTPS scheme, we assume a local file, return the
        # absolute path of the file
        if not parsed_uri:
            log_safely(f"URI appears to be a local file: {uri}", logs)
            path_to_file = Path(uri)
            if not path_to_file.exists():
                raise FileNotFoundError(f"File not found at {path_to_file.absolute()}")
            return FinderResult(str(path_to_file.resolve()), None)

        # if we reach this point.we are dealing with remote file.

        # If the URI is a valid HTTP or HTTPS URI, check if the URI is reachable.
        try:
            response = httpx.head(
                parsed_uri.geturl(),
                timeout=self.http_timeout,
                headers=self.http_headers,
            )
        except httpx.ConnectError:
            raise UnreachableCarbonTxtFile(
                f"Could not connect to {parsed_uri.geturl()}."
            )

        except Exception as ex:
            logger.exception(f"Unexpected error fetching {parsed_uri.geturl()}: {ex}")
            raise UnreachableCarbonTxtFile(
                f"Could not connect to {parsed_uri.geturl()}."
            )

        if response.status_code > 399:
            raise UnreachableCarbonTxtFile(
                f"HTTP error {response.status_code} when connecting to {parsed_uri.geturl()}"
            )

        return FinderResult(parsed_uri.geturl(), None)
