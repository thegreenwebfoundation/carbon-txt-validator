# Plugins

The Carbon.txt Validator is designed to have its functionality [extended using its plugin system](#extending-the-carbontxt-validator-with-plugins).

In fact, some of the core functionality is implemented as plugins.

```{contents}
:class: this-will-duplicate-information-and-it-is-still-useful-here
:depth: 3
```

See [using plugins](./using_plugins.md) for instructions on using the validator with various plugins


## Bundled Plugins with the Carbon.txt Validator

Some plugins are bundled into the main carbon.txt validator package, but others are avaiable online. We maintain a curated list below.

### `carbon-txt-greenweb-csrd` - the 'Green Web CSRD' plugin

The CSRD plugin for the carbon.txt validator is one of the default plugins bundled in with the validator. The [source code for the plugin](https://github.com/thegreenwebfoundation/carbon-txt-validator/blob/main/src/carbon_txt/process_csrd_document.py) as is [the CSRD processor it uses to parse reports](https://github.com/thegreenwebfoundation/carbon-txt-validator/blob/main/src/carbon_txt/processors.py#L30). Under the hood, it uses [Arelle, a report parsing tool certified by the XBRL Foundation](https://arelle.readthedocs.io).

```{admonition} Info

#### What is the CSRD, and why is it relevant?

Starting in 2025, organisations in Europe that are covered by a new law about sustainability reporting, the Corporate Sustainability Reporting Directive, need to publish an annual report containing data about their environnmental and social impact, using a standardised reporting system - the European Sustainability Reporting Standards. This should be published with the annual management report, which shares the usual financial information you might expect a large organisation to publish each year.

These reports are published in a standardised format, and in a structured language, XBRL. This means the data can be queried if you have the right software.

This page shows how to use the validator to query these reports for specific kinds of data.

---
```


## External plugins

### `carbon-txt-check-online` - the "check Online" plugin

A demonstration plugin, designed notify if linked files in a carbon.txt file are still reachable. Built as a reference for [our tutorials for building carbon-txt plugins](https://developers.thegreenwebfoundation.org/carbon-txt/tutorials/make-a-public-plugin/).

- Download from PyPi: [https://pypi.org/project/carbon-txt-check-online](https://pypi.org/project/carbon-txt-check-online)
- See the source on github: [https://github.com/thegreenwebfoundation/carbon-txt-check-online](https://github.com/thegreenwebfoundation/carbon-txt-check-online)

### `carbon-txt-download-disclosures` - the "download disclosures" plugin

A plugin designed to fetch a linked disclosures in a carbon.txt file, like sustainabilty reports, energy origin certificates, web pages and so on and make a copy, for local processing, like extacting text, running an LLM against and so on.

- Download from PyPi: [https://pypi.org/project/carbon-txt-download-disclosures](https://pypi.org/project/carbon-txt-download-disclosures)
- See the source on github: [https://github.com/thegreenwebfoundation/carbon-txt-download-disclosures](https://github.com/thegreenwebfoundation/carbon-txt-download-disclosures)


----
