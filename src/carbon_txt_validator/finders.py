import httpx
import dns.resolver
import tomllib as toml
from pathlib import Path
from urllib.parse import urlparse, ParseResult
from typing import Optional
import logging
import rich

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
        # if have it, return that
        try:
            dns_record = dns.resolver.resolve(domain, "TXT")
            if dns_record:
                url = dns_record[0].strings[0].decode()
                rich.print(url)
                return url

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

    def resolve_uri(self, uri: str) -> str:
        """
        Accept a URI pointing to a carbon.txt file, and return the final
        resolved URI, following any 'via' referrers or similar.
        """

        # check if the uri looks like one we might reach over HTTP / HTTPS
        parsed_uri = self._parse_uri(uri)

        # if there is no http or https scheme, we assume a local file
        if not parsed_uri:
            path_to_file = Path(uri)
            return str(path_to_file.resolve())

        response = httpx.head(parsed_uri.geturl())
        if response.status_code == 200:
            return parsed_uri.geturl()

        # fallback to doing retry or notifying us if the domain is unreachable
        # TODO:

        # check if there is a via header
        # TODO: do we follow multiple 'via' headers? If so, how many hops do we follow before we timeout?
