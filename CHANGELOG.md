# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Fixed, Changed, Added, Removed, Fixed, Security

## Unreleased



### Changed

- Update pre-commit hooks to 0.5.0 and Ruff to 0.8.0

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
