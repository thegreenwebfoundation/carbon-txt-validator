from django.db import models


class ValidationLogEntry(models.Model):
    """
    This class represents an attempt to validate a domain,
    url, or file via the API. It is called from LogValidationMiddleware,
    and used to populate the database for later analysis and tracking the
    uptake of the carbon.txt stanard.
    """

    class Source(models.TextChoices):
        VALIDATOR_API = "validator_api"
        PROVIDER_PORTAL = "provider_portal"
        UNKNOWN = "unknown"

    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    endpoint: models.CharField = models.CharField(max_length=255, null=True, blank=True)
    domain: models.CharField = models.CharField(
        max_length=255, blank=True, null=True
    )  # Length limit from RFC 1035
    url: models.TextField = models.TextField(blank=True, null=True)
    success: models.BooleanField = models.BooleanField(blank=True, null=True)
    source: models.CharField = models.CharField(
        choices=Source, default=Source.UNKNOWN, blank=False, null=False, max_length=255
    )
