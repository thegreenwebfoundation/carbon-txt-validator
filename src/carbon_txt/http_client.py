from typing import Optional
import importlib.metadata

import httpx


class HTTPClient:
    """
    This class wraps httpx, and ensures that we use the configured timeout and http user User-Agent,
    everywhere that the validator makes HTTP requests.
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

    def get(self, *args, **kwargs) -> httpx.Response:
        return httpx.get(*args, **self.all_request_kwargs(kwargs))

    def head(self, *args, **kwargs) -> httpx.Response:
        return httpx.head(*args, **self.all_request_kwargs(kwargs))

    def all_request_kwargs(self, kwargs):
        return kwargs | {"timeout": self.http_timeout, "headers": self.http_headers}

    @property
    def http_headers(self) -> dict[str, str]:
        return {"User-Agent": self.http_user_agent}
