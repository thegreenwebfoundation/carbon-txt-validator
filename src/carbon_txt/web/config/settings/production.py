from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost", ".localhost", ".greenweb.org"]

WSGI_APPLICATION = "carbon_txt.web.config.wsgi.application"
ROOT_URLCONF = "carbon_txt.web.config.urls"
