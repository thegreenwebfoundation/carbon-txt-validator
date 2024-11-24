# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Fixed, Changed, Added, Removed, Fixed, Security

## Unreleased

### Added

- Add architecture docs for how the validator is built [#7e39de2](https://github.com/thegreenwebfoundation/carbon-txt-validator/commit/7e39de25f96d439b03a4a907337a6110a5affd11)

### Fixed

- Fix handling of non TOML responses when carbon.txt files are served [#33]()

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
