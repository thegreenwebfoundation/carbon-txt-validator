import json
from typing import Callable
from urllib.parse import urlparse

import structlog
from django.http import HttpRequest, HttpResponse

from carbon_txt.web.validation_logging.models import ValidationLogEntry


class LogValidationMiddleware:
    """
    Middleware to log the domains requested by users of the carbon.txt validator.
    This enables us to track use of the standard, but also which domains are implementing it.
    All requests to `/api/validate` endpoints are tracked, along with the `success` flag
    returned in the response. In the case where a URL was supplied, we also log the
    url tested and the domain.
    """

    def __init__(
        self, get_response: Callable, logger=None, log_model_class=ValidationLogEntry
    ):
        if logger is None:
            logger = structlog.get_logger(__name__)
        self.get_response = get_response
        self.logger = logger
        self.log_model_class = log_model_class

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if "api/validate" in request.path:
            try:
                self.log_validation(request, response)
            except Exception as ex:
                self.logger.exception(f"Validation logging failed with exception: {ex}")
        return response

    def log_validation(self, request: HttpRequest, response: HttpResponse):
        """
        This method parses out the relevant details of the request and response
        (url, domain, and success) and logs them in grafana as a validation_request
        event, as well as adding a log entry in the database. we can then use these
        to track uptake of the carbon.txt standard.
        """
        request_json = json.loads(request.body)
        response_json = json.loads(response.content)
        log_params = {}
        log_params["endpoint"] = request.path
        log_params["success"] = response_json.get("success")

        if "url" in response_json:
            log_params["url"] = response_json["url"]
        elif "url" in request_json:
            log_params["url"] = request_json["url"]

        if "domain" in request_json:
            log_params["domain"] = request_json["domain"]
        elif "url" in request_json:
            log_params["domain"] = urlparse(log_params["url"]).netloc

        self.logger.info("validation_request", **log_params)
        log_entry = self.log_model_class(**log_params)
        log_entry.save()
