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
        """
        Setup mocks for the request, response and logger.
        """
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
        """
        The middleware calls the underlying get_response function
        """

        # Given I have installed the middleware
        self.setup(path)

        # When I make a request
        self.middleware(self.request)

        # The underlying application should be called with the request
        self.get_response.assert_called_with(self.request)

    @pytest.mark.parametrize("path", all_paths)
    def test_returns_the_response(self, path):
        """
        The middleware returns the value returned by the underlying get_response function
        """

        # Given I have installed the middleware
        self.setup(path)

        # When I make a request
        returned = self.middleware(self.request)

        # The response from the underlying application should be returned to the client.
        assert returned == self.response

    @pytest.mark.parametrize("path", validation_paths)
    def test_exceptions_caught_and_original_response_returned(self, path):
        """
        Errors raised during the logging process are silently logged
        """

        # Given an error occurs when attempting to log the validation request
        response = {"success": True, "logs": ["This is the original response"]}
        self.setup(path, response=response)
        self.logger.info.side_effect = Exception(
            "There was an error logging the response!"
        )

        # When I make the request
        returned = self.middleware(self.request)

        # Then the underlying application response should be returned as normal
        assert json.loads(returned.content) == response

        # And the error should be logged
        self.logger.warn.assert_called()

    def test_non_api_validation_requests_not_logged(self):
        """
        Requests that are not to validation endpoints are not logged
        """

        # Given a request to a URL which is not a validation endpoint
        self.setup(path="/not/validation")

        # When the request is made
        self.middleware(self.request)

        # Then nothing is logged
        self.logger.info.assert_not_called()
        self.logger.warn.assert_not_called()

    def test_validate_file_requests_logged_without_url_or_domain(self):
        """
        File validation requests are logged, without any url or domain metadata.
        """

        # Given a valid request for a file validation
        self.setup(
            path="/api/validate/file",
            request={"text_content": ""},
            response={"success": True},
        )

        # When the request is made
        self.middleware(self.request)

        # A validation request is logged, with the endpoint details and the success status of the validation.
        self.logger.info.assert_called_with(
            "validation_request", endpoint="/api/validate/file", success=True
        )

    def test_validate_url_requests_logged_with_url_and_domain(self):
        # Given a valid request for a url validation

        self.setup(
            path="/api/validate/file",
            request={"url": "https://www.example.com/carbon.txt"},
            response={"success": True},
        )

        # When the request is made
        self.middleware(self.request)

        # A validation request is logged, with the endpoint details, the success status
        # of the validation. the domain and url.
        self.logger.info.assert_called_with(
            "validation_request",
            endpoint="/api/validate/file",
            url="https://www.example.com/carbon.txt",
            domain="www.example.com",
            success=True,
        )
