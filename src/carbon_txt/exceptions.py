class InsecureKeyException(Exception):
    """Raised when the default SECRET_KEY is used in a production django server environment"""

    pass
