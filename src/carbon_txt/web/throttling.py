from django.conf import settings
from ninja.throttling import AuthRateThrottle

class AuthRateThrottleWithInternalOverride(AuthRateThrottle):
    def allow_request(self, request):
        if not settings.REQUIRE_API_KEY:
            return True
        if request.auth and "privilege_level" in request.auth and request.auth["privilege_level"] == "internal":
            return True
        return super().allow_request(request)
