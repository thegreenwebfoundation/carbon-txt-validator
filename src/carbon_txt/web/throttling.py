from django.conf import settings
from ninja.throttling import AuthRateThrottle
from structlog import get_logger
logger = get_logger(__file__)

class AuthRateThrottleWithInternalOverride(AuthRateThrottle):
    def allow_request(self, request):
        if not settings.REQUIRE_API_KEY:
            return True
        if request.auth and "privilege_level" in request.auth and request.auth["privilege_level"] == "internal":
            return True
        result = super().allow_request(request)
        if not result:
            if request.auth:
                username = request.auth.get("username")
                user_id = request.auth.get("user_id")
                logger.warning("request_throttled", username=username, user_id=user_id, path=request.path)
        return result
