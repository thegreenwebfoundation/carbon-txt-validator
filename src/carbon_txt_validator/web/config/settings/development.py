from .base import *  # noqa

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

WSGI_APPLICATION = "carbon_txt_validator.web.config.wsgi.application"
ROOT_URLCONF = "carbon_txt_validator.web.config.urls"
