from django.http import HttpRequest, HttpResponse
from typing import Callable


class AddTrailingSlashMiddleware:
    """
    Middleware to add a trailing slash to specific API endpoints, but
    keep the other endpoints like /api/docs and api/openapi.json as they are.

    For more, see the links below
    https://github.com/vitalik/django-ninja/issues/1058
    https://docs.djangoproject.com/en/5.1/topics/http/middleware/
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Note: 'validate' is the endpoint that requires a trailing slash.
        # we still want /api/docs and /api/openapi.json to work
        # without a trailing slash.
        if "api/validate" in request.path and not request.path.endswith("/"):
            request.path_info = request.path = f"{request.path}/"

        response = self.get_response(request)
        return response
