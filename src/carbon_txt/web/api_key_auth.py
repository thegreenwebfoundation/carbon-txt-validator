import httpx
from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyHeader
from structlog import get_logger

logger = get_logger()


def introspect_key(key: str | None) -> dict | None:
    """
    Hands off to the admin portal API key introspection API to authorize
    the user's API key if authentication is enabled.
    """
    if not settings.REQUIRE_API_KEY:
        return {"active": True}
    if key:
        try:
            prefix, _ = key.split(".")
            resp = httpx.post(
                settings.API_KEY_INTROSPECTION_URL,
                json={"token": key},
                headers={"X-GWF-Shared-Secret": settings.GWF_SHARED_SECRET},
                timeout=5.0,
            )
            resp.raise_for_status()
            body = resp.json()
            if body["active"]:
                return body

        except httpx.HTTPStatusError as ex:
            # A non-200 respoonse from the introspection API
            logger.error(f"Introspection returned {ex.response.status_code} for key prefix {prefix}: {ex}")
        except httpx.HTTPError as ex:
            # A lower-level network error
            logger.error(f"Network error contacting introspection endpoint for key prefix {prefix}: {ex}")
        except KeyError as ex:
            # The request returned JSON without an "active" key
            logger.error(f"Malformed introspection response for key prefix {prefix}: {ex}")
        except ValueError:
            # This is raised in the call to key.split - GWF keys are in the
            # format gwf_xxxxxx.xxxxx.. - so this isn't a real one.
            logger.exception(f"Malformed API key provided: \"{key[0:10]}...\"")
        except Exception as ex:
            # Anything else that might go wrong - we err on the side of caution.
            logger.exception(
                f"Unexpected error authorizing key with prefix {prefix}: {ex}"
            )
    return None


class APIKeyHeaderAuth(APIKeyHeader):
    param_name = "X-Api-Key"

    def authenticate(self, request: HttpRequest, key: str) -> dict | None:
        return introspect_key(key)
