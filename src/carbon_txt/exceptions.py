class InsecureKeyException(Exception):
    """
    Raised when the default SECRET_KEY is used in a
    production django server environment
    """

    pass


class UnreachableCarbonTxtFile(Exception):
    """
    Raised when we can't reach the carbon.txt file
    """

    pass


class NotParseableTOML(Exception):
    """
    Raised when we have a response at a the given carbon txt
    URL, but it is not parsable TOML file
    """

    pass
