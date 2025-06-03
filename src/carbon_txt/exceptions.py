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
    Raised when we have a response at the given carbon txt
    URL, but it is not parsable TOML file.
    """

    pass


class NotParseableTOMLButHTML(Exception):
    """
    Raised when we have a parsed HTML string when we expected
    TOML instead. Used to catch "Not Found" style pages, or fallback
    index pages that return with a 200 OK status code when there is
    no carbon.txt file at the expected /carbon.txt or
    ./.well-known/carbon.txt paths.
    """

    pass


class NoMatchingDatapointsError(ValueError):
    """
    Thrown when a report does not have the expected datapoint.

    This could be because a data point is either
    1. missing, or
    2. intentionally omitted because it was deemed immaterial
    """

    def __init__(
        self,
        message: str,
        datapoint_short_code: str,
        datapoint_readable_label: str,
    ) -> None:
        super().__init__(message)
        self.datapoint_short_code = datapoint_short_code
        self.datapoint_readable_label = datapoint_readable_label

    def __dict__(self):
        return {
            "message": self.args[0],  # ValueError stores the message in args
            "datapoint_short_code": self.datapoint_short_code,
            "datapoint_readable_label": self.datapoint_readable_label,
        }


class NoLoadableCSRDFile(ValueError):
    """
    Thrown when a the link CSRD file can't be loaded by Arelle.
    """

    pass
