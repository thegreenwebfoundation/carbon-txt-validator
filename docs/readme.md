# How carbon.txt is designed.

The carbon.txt validator is split into a series of components, with clear divisions of responsibility

- **Finders**: Finders are responsible for accepting a domain or URI, and resolving it to the final URI where a carbon.txt file is accessible, for fetching and reading.
- **Parsers**: Parsers are responsible for parsing carbon.txt files, then making sure they valid and conform to the required data schema.
- **Processors**(s): Processors are responsible for parsing specific kinds of linked documents, and data, and returning a valid data structure.
