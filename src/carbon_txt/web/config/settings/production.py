from .base import *

DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost", ".localhost", ".greenweb.org"]

WSGI_APPLICATION = "carbon_txt.web.config.wsgi.application"
ROOT_URLCONF = "carbon_txt.web.config.urls"


# switch to using a logger better suited for production
LOGGING["handlers"]["console"] = {  # type: ignore
    "class": "logging.StreamHandler",
    "formatter": "key_value",
}
