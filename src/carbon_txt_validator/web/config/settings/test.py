from .base import *  # noqa

INTERNAL_IPS = ["127.0.0.1"]
ALLOWED_HOSTS.extend(["127.0.0.1", "localhost"])  # noqa

WSGI_APPLICATION = "carbon_txt_validator.web.config.wsgi.application"
ROOT_URLCONF = "carbon_txt_validator.web.config.urls"
