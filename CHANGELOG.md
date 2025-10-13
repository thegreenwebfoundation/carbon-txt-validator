# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Fixed, Changed, Added, Removed, Fixed, Security

## Unreleased

## [0.0.19]

### Added

 - Add special case fallback lookup for www. subdomains, as detailed in ADR 04

## [0.0.18]

### Added

 - Add optional http_user_agent argument to FileFinder and CarbonTxtValidator class, applied to all HTTP calls made.

## [0.0.17]

### Added

 - Add http_timeout argument to FileFinder and CarbonTxtValidator class, defaulting to 5 seconds, and applied to all HTTP calls made.

## [0.0.16]

###  Added
 - Expose delegation method on domain endpoint.
 - Add distinguish between failing 200 and 404 responses
 - Add handling HTML served at example.org/carbon.txt

### Changed
 - Ensure DNS record delegation takes priority

### Fixed
 - add pyright config to get rid of spurious typecheck warnings
 - Stop the CI double runs
 - Add github action for deploying the service


## [0.0.15]

### Changed

 - Use of 'Via' HTTP header and `carbon-txt` DNS TXT record deprecated in favour of new `Carbon-Txt-Location` HTTP header and `carbon-txt-location` DNS TXT record.
 - Formalise the order of priority in carbon.txt domain lookups: Local file in root, followed by local file in `.well-known`, followed by DNS TXT record, followed by HTTP Header.
 - Ensure that checks for a specific carbon.txt URL do not follow the domain delegation lookup logic

## [0.0.14]


### Added

- Logging of validation requests in the API to database and stdout
- API endpoint for validation of domains
- Sample output for issue 8 raised by Andy
- Extra documentation for creating external plugin

### Changed

- Never follow redirection when validating a URL
- Update our plugin listings, and remove duplicate tutorial
- Update docs, linking to new site
- Tidy up docs on the GreenwebCSRD processor
- Replace Credentials with Disclosures

### Fixed

- Fix readthedocs build script
  Use HTTP and DNS mocks in test suite

## [0.0.13]

### Changed

- Refactor the CSRD Processor for easier plugins
- Tidy up logging so it's in one file

## [0.0.12]

### Added

- Add new defaults for seeing logger output
- Add safer loading of plugins
- Add a guidance and screenshots for using Bruno for GUI API tests
- Add example Bruno tests
- Add the ESRS excel file with our data name mappings
- Add first pass at docs on using bundled plugins
- Add first class and test for parsing CSRD files
- Add exploration of fetching values from online CSRD report
- Add missing Apache license

### Changed

- Update docs to flesh out usage instructions
- Update pre-commit hooks to 0.5.0 and Ruff to 0.8.0
- Update tests and code for name change
- Rework the docs for people using validator
- Update API to return sanitized error notifications
- Update marimo demo to for choosing different datapoints

### Fixed

- Fix case of handling multiple validation errors

## [0.0.11]

### Added

- Add architecture docs for how the validator is built [#7e39de2](https://github.com/thegreenwebfoundation/carbon-txt-validator/commit/7e39de25f96d439b03a4a907337a6110a5affd11)
- Add new Validator class that wraps the behaviour exposed to the CLI and API, making it more consistent [#34](https://github.com/thegreenwebfoundation/carbon-txt-validator/pull/34)
- Add new logging behaviour in the validator [#20](https://github.com/thegreenwebfoundation/carbon-txt-validator/issue/20)
- Add new API checker notebook [#35](https://github.com/thegreenwebfoundation/carbon-txt-validator/pull/35)

### Changed

- Refactored the Finder and TOML Parser classes, so that the Finder is always responsible for fetching files, and the Validator responsible for parsing strings and datastructures [#34](https://github.com/thegreenwebfoundation/carbon-txt-validator/pull/34)

### Fixed

- Fix handling of non TOML responses when carbon.txt files are served [#33](https://github.com/thegreenwebfoundation/carbon-txt-validator/pull/33)

## [0.0.10]

### Added

- Extra details in the runbook section of the docs for operating the carbon.txt API server

### Fixed

- Fix mismatch between API and CLI responses for certain lookups [#31](https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/30git)

## [0.0.9]

### Fixed

- Fix ordering of optional params when used with Granian webserver

## [0.0.8]

### Changed

- Switch to using more detailed exceptions

### Added

- Add support for generating JSON Schema representation with CLI and API
- Add support for using Sentry to track exceptions, performance and so on.
- Add github action for automated publishing of releases to Pypi

### Fixed

- Respect the provided `port` and `host` values with `carbon-txt serve` [#27](https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/27)



## [0.0.7]

### Added

- First release using the formal changelog
