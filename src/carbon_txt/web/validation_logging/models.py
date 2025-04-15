from django.db import models


class ValidationLogEntry(models.Model):
    """
    This class represents an attempt to validate a domain,
    url, or file via the API. It is called from LogValidationMiddleware,
    and used to populate the database for later analysis and tracking the
    uptake of the carbon.txt stanard.
    """

    timestamp = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=255)
    domain = models.CharField(
        max_length=255, blank=True, null=True
    )  # Length limit from RFC 1035
    url = models.TextField(blank=True, null=True)
    success = models.BooleanField(blank=True, null=True)
