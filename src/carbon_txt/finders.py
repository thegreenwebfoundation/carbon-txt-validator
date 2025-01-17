import pathlib
from pathlib import Path
from typing import Optional
from urllib.parse import ParseResult, urlparse

import dns.resolver
import httpx
import rich  # noqa
from .exceptions import UnreachableCarbonTxtFile

from . import parsers_toml

from structlog import get_logger

import logging

logger = get_logger()


parser = parsers_toml.CarbonTxtParser()


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

    def _parse_uri(self, uri: str) -> Optional[ParseResult]:
        """
        Return a parsed URI object if the URI is valid, otherwise return None
        """
        parsed_uri = urlparse(uri)

        if parsed_uri.scheme in ("http", "https"):
            return parsed_uri

        return None

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
                if txt_record.startswith("carbon-txt"):
                    # pull out our url to check
                    _, txt_record_body = txt_record.split("=")

                    domain_hash_check = txt_record_body.split(" ")

                    # check for delegation with no domain hash
                    if len(domain_hash_check) == 1:
                        override_url = domain_hash_check[0]
                        logger.info(
                            f"Found an override_url to use from the DNS lookup: {override_url}"
                        )
                        return override_url

                    # check for delegation WITH a domain hash
                    if len(domain_hash_check) == 2:
                        override_url = domain_hash_check[0]

                        # TODO add verification of domain hash
                        domain_hash = domain_hash_check[1]  # noqa

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

    def _check_for_via_delegation(self, response: httpx.Response) -> Optional[str]:
        """
        Check for a 'via' header in the response, and return the URL in the 'via' header if present
        """

        if "via" in response.headers:
            via_header = response.headers.get("via")

            version, via_url, *rest = via_header.split(" ")
            logger.info(f"Found a 'via' header, following to: {via_url}")

            try:
                parsed_url = httpx.URL(via_url)
                return str(parsed_url)
            except httpx.InvalidURL:
                logger.error(f"Invalid URL in 'via' header: {via_url}")
                return None

        return None

    def fetch_carbon_txt_file(self, uri: str, logs=None) -> str:
        """
        Accept a URI and either fetch the file over HTTP(S), or read the local file.
        Return a string of contents of the remote carbon.txt file, or the local file.
        """
        if uri.startswith("http"):
            try:
                response = httpx.get(uri)
                result = response.text
                return result
            except httpx._exceptions.ConnectError as ex:
                raise UnreachableCarbonTxtFile(
                    f"Could not connect to {uri}. Error was: {ex}"
                )

        if pathlib.Path(uri).exists():
            return pathlib.Path(uri).read_text()

        raise ValueError(f"Could not fetch file contents at {str}")

    def resolve_domain(self, domain: str, logs=None) -> str:
        """
        Accepts a domain, and returns a URI to fetch a carbon.txt file from.

        Follows delegation logic from DNS TXT records, and the 'via' header in
        HTTP responses to resolve to a final URL for a carbon.txt file.
        """

        log_safely(f"Trying a DNS delegated lookup for domain {domain}", logs)
        if uri_from_domain := self._lookup_dns(domain):
            log_safely(f"New lookup found for domain {domain}: {uri_from_domain}", logs)
            return self.resolve_uri(uri_from_domain)

        # otherwise we look for a carbon.txt file at the root of the domain.
        # If that isn't there try a fallback to one at the `.well-known`` path
        # following the well-known convention
        default_paths = ["/carbon.txt", "/.well-known/carbon.txt"]

        for url_path in default_paths:
            message = f"Checking if a carbon.txt file is reachable at https://{domain}{url_path}"
            log_safely(message, logs)
            uri = urlparse(f"https://{domain}{url_path}")
            response = httpx.head(uri.geturl())
            if response.status_code == 200:
                log_safely(f"New Carbon text file found at: {uri.geturl()}", logs)
                return uri.geturl()

        # if a path has the 'via' header, it suggests a managed service or proxy
        # follow that path to fetch the active carbon.txt file
        log_safely(f"Checking for a 'via' header in the response: {response.url}", logs)
        if delegated_via_carbon_file_url := self._check_for_via_delegation(response):
            log_safely(
                f"Found a 'via' header, following to {delegated_via_carbon_file_url}",
                logs,
            )
            return delegated_via_carbon_file_url

        raise UnreachableCarbonTxtFile(
            f"Unable to find a valid carbon.txt file at the domain {domain}"
        )

    def resolve_uri(self, uri: str, logs=None) -> str:
        """
        Accept a URI pointing to a carbon.txt file, and return the final
        resolved URI, following any 'via' referrers or similar.

        This is a recursive function, so it expects to be called, following redirections until
        it either arrives at a 200 OK response, or a non 400/500.

        This does NOT try to fetch the file, just resolve the final URI to fetch it from
        """

        # check if the uri looks like one we might reach over HTTP / HTTPS
        parsed_uri = self._parse_uri(uri)

        # if there is no http or https scheme, we assume a local file, return the
        # absolute path of the file
        if not parsed_uri:
            log_safely(f"URI appears to be a local file: {uri}", logs)
            path_to_file = Path(uri)
            if not path_to_file.exists():
                raise FileNotFoundError(f"File not found at {path_to_file.absolute()}")
            return str(path_to_file.resolve())

        # if we reach this point.we are dealing with remote file.
        # check for delegation before returning the final URI

        # check for DNS TXT record delegation first, and call this function again
        # with the resolved URI, to follow the delegation
        log_safely(f"Trying a DNS delegated lookup for URI: {parsed_uri.netloc}", logs)

        if delegated_dns_uri := self._lookup_dns(parsed_uri.netloc):
            log_safely(
                f"Found new carbon.txt URL via DNS lookup: {delegated_dns_uri}", logs
            )
            return self.resolve_uri(delegated_dns_uri)
        log_safely("None found. Continuing.", logs)

        # If the URI is a valid HTTP or HTTPS URI, check if the URI is reachable.
        # If there is a 'via' header in the response, we follow that
        try:
            response = httpx.head(parsed_uri.geturl())
        except httpx._exceptions.ConnectError:
            raise UnreachableCarbonTxtFile(
                f"Could not connect to {parsed_uri.geturl()}."
            )

        except Exception as ex:
            logger.exception(f"Unexpected error fetching {parsed_uri.geturl()}: {ex}")
            raise UnreachableCarbonTxtFile(
                f"Could not connect to {parsed_uri.geturl()}."
            )

        # check if there is a 'via' header in the response containing a domain to delegate
        # the carbon.txt file lookup to
        log_safely(f"Checking for a 'via' header in the response: {response.url}", logs)
        if via_domain := self._check_for_via_delegation(response):
            log_safely(
                f"Found a new URL from the 'via' header in response: {via_domain}", logs
            )
            return self.resolve_uri(via_domain)
        log_safely("None found. Continuing.", logs)

        # if the response is a 200 OK, return the URI
        response.raise_for_status()

        return parsed_uri.geturl()
