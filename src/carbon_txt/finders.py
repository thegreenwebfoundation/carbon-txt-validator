import httpx
import dns.resolver
from pathlib import Path
from urllib.parse import urlparse, ParseResult
from typing import Optional
import logging
import rich  # noqa

from .exceptions import UnreachableCarbonTxtFile

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


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

    def _lookup_dns(self, domain):
        """Try a DNS TXT record lookup for the given domain"""

        # look for a TXT record on the domain first
        # if there is a valid TXT record it, return that
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

    def resolve_domain(self, domain) -> str:
        """
        Accepts a domain, and returns a URI to fetch a carbon.txt file from.
        """

        uri_from_domain = self._lookup_dns(domain)

        if uri_from_domain:
            return self._parse_uri(uri_from_domain).geturl()

        # otherwise we look for a carbon.txt file at the root of the domain, then fallback to
        # one at the .well-known path following the well-known convention
        default_paths = ["/carbon.txt", "/.well-known/carbon.txt"]

        for url_path in default_paths:
            uri = urlparse(f"https://{domain}{url_path}")
            response = httpx.head(uri.geturl())
            if response.status_code == 200:
                return uri.geturl()

        # if a path has the 'via' header, it suggests a managed service or proxy
        # follow that path to fetch the active carbon.txt file

        # TODO allow file on the domain to override the one specificed in a 'via'

    def _check_for_via_delegation(self, url: httpx.URL) -> httpx.URL:
        """
        Check for a 'via' header in the response, and return the URL in the 'via' header if present
        """

        if "via" in url.headers:
            via_header = url.headers.get("via")

            version, via_url, *rest = via_header.split(" ")
            logger.info(f"Found a 'via' header, following to {via_url}")

            try:
                parsed_url = httpx.URL(via_url)
                return str(parsed_url)
            except httpx.InvalidURL:
                logger.error(f"Invalid URL in 'via' header: {via_url}")
                return None

        return None

    def resolve_uri(self, uri: str) -> str:
        """
        Accept a URI pointing to a carbon.txt file, and return the final
        resolved URI, following any 'via' referrers or similar.
        """

        # check if the uri looks like one we might reach over HTTP / HTTPS
        parsed_uri = self._parse_uri(uri)

        # if there is no http or https scheme, we assume a local file, return the
        # absolute path of the file
        if not parsed_uri:
            path_to_file = Path(uri)
            if not path_to_file.exists():
                raise FileNotFoundError(f"File not found at {path_to_file.absolute()}")
            return str(path_to_file.resolve())

        # if the URI is a valid HTTP or HTTPS URI, we check if the URI is reachable
        # and if there is a 'via' header in the response, we follow that
        try:
            response = httpx.head(parsed_uri.geturl())
        except httpx._exceptions.ConnectError:
            raise UnreachableCarbonTxtFile(
                f"Could not connect to {parsed_uri.geturl()}."
            )
        # catch any errors from the request
        response.raise_for_status()

        # check if there is a 'via' header in the response containing a domain to delegate
        # the carbon.txt file lookup to
        if via_domain := self._check_for_via_delegation(response):
            return via_domain

        if response.status_code == 200:
            return parsed_uri.geturl()
