import json
import pytest
from unittest.mock import MagicMock

from django.http import HttpRequest, HttpResponse
from structlog.stdlib import BoundLogger

from carbon_txt.web.middleware import LogRequestedDomainMiddleware

validation_paths = ["/api/validate/path", "/api/validate/file"]
all_paths = ["/not/validation"] + validation_paths


class TestLogRequestedDomainMiddleware:
    def setup(self, path, request={}, response={}):
        self.request = MagicMock(HttpRequest)
        self.request.path = path
        self.request.body = json.dumps(request).encode("utf-8")
        self.response = MagicMock(HttpResponse)
        self.response.content = json.dumps(response).encode("utf-8")
        self.get_response = MagicMock()
        self.get_response.return_value = self.response
        self.logger = MagicMock(BoundLogger)

        self.middleware = LogRequestedDomainMiddleware(self.get_response, self.logger)

    @pytest.mark.parametrize("path", all_paths)
    def test_calls_the_get_response_callable_with_the_request(self, path):
        self.setup(path)
        self.middleware(self.request)

        self.get_response.assert_called_with(self.request)

    @pytest.mark.parametrize("path", all_paths)
    def test_returns_the_response(self, path):
        self.setup(path)

        returned = self.middleware(self.request)

        assert returned == self.response

    @pytest.mark.parametrize("path", validation_paths)
    def test_exceptions_caught_and_original_response_returned(self, path):
        response = {"success": True, "logs": ["This is the original response"]}
        self.setup(path, response=response)
        self.logger.info.side_effect = Exception(
            "There was an error logging the response!"
        )

        returned = self.middleware(self.request)

        assert json.loads(returned.content) == response
        self.logger.warn.assert_called()

    def test_non_api_validation_requests_not_logged(self):
        self.setup(path="/not/validation")

        self.middleware(self.request)

        self.logger.info.assert_not_called()
        self.logger.warn.assert_not_called()

    def test_validate_file_requests_logged_without_url_or_domain(self):
        self.setup(
            path="/api/validate/file",
            request={"text_content": ""},
            response={"success": True},
        )

        self.middleware(self.request)

        self.logger.info.assert_called_with(
            "validation_request", endpoint="/api/validate/file", success=True
        )

    def test_validate_url_requests_logged_with_url_and_domain(self):
        self.setup(
            path="/api/validate/file",
            request={"url": "https://www.example.com/carbon.txt"},
            response={"success": True},
        )

        self.middleware(self.request)

        self.logger.info.assert_called_with(
            "validation_request",
            endpoint="/api/validate/file",
            url="https://www.example.com/carbon.txt",
            domain="www.example.com",
            success=True,
        )
