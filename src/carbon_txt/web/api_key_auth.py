import httpx
from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyHeader, APIKeyQuery
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
            resp = httpx.post(
                settings.API_KEY_INTROSPECTION_URL,
                json={"token": key},
                headers={"X-GWF-Shared-Secret": settings.GWF_SHARED_SECRET},
            )
            body = resp.json()
            if body["active"]:
                return body
        except Exception as ex:
            prefix, _ = key.split(".")
            logger.exception(
                f"Unexpected error authorizing key with prefix {prefix}: {ex}"
            )
    return None


class APIKeyHeaderAuth(APIKeyHeader):
    param_name = "X-Api-Key"

    def authenticate(self, request: HttpRequest, key: str) -> dict | None:
        return introspect_key(key)


class APIKeyQueryAuth(APIKeyQuery):
    param_name = "api_key"

    def authenticate(self, request: HttpRequest, key: str) -> dict | None:
        return introspect_key(key)
