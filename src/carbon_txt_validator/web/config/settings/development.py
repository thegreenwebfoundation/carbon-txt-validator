from .base import *  # noqa

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

WSGI_APPLICATION = "carbon_txt_validator.web.config.wsgi.application"
ROOT_URLCONF = "carbon_txt_validator.web.config.urls"

# CORS
# for docs see:
# https://github.com/adamchainz/django-cors-headers
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Uncomment this to allow connections from any 'local' domain, like
# if you are using '.dev' or '.local' domain with a reverse proxy
# like Caddy or Nginx
# CORS_ALLOW_ALL_ORIGINS = True
