# ADR 6: Representing certification schemes in carbon.txt

## Status

Draft

## Context

We've been considering how best to express certification schemes in carbon.txt - voluntary programmes, such as B-corp, SCI-web, Greenmark alliance, Blue Angel, or TCO Certified Cloud, by which providers of digital services make certain commitments about energy use, emissions, or sustainability in general, and receive an independently verified certification that they comply with those commitments.

After some consultation with users of carbon.txt and other stakeholders - certificate granting and certified organizations, we arrived at a core set of requirements:

- Applicable certification schemes need to be represented in carbon.txt, identified, minimally, by a URL to a page which details the granting organizaiton and the requirements for certification.
- Particular disclosures need to be able to make reference to these certification schemes, to signal either that they represent a _certification_ under that scheme, or that they offer evidence accepted by that scheme. Particular disclosures might refer to multiple different certification schemes (e.g. in the case where an organization has received two different independent certifications with overlapping )
- Certifications under a certification scheme are valid for a finite period of time which must be captured.
- Optionally, users should be able to provide a narrative title and description for the certification schemes detailed in their files.

## Decision

Certification schemes will be represented by a new root-level section in the carbon.txt file, identified, minimally, by a URL to a page which details (ideally) the requirements for certification, or at very least, provides details of the granting organization. These certification schemes will also be given an arbitary (but unique in the scope of the current carbon.txt file) alphanumeric identifier which can be used in the disclosure section to make reference to them:

```toml
[org]
certification_schemes = [
	{ id="b-corp", url="https://bcorpspain.es" },
]
```

Optionally, users can provide a title and description to the certification schemes detailed:

```toml
[org]
certification_schemes = [
	{ id="b-corp", url="https://bcorpspain.es", title="B Corp", description="B corp is a community of businesses that meet verified social, environmental, and governance standards. Together, our movement is working towards a more inclusive, equitable, and fair economic system." },
]
```

Once a certification scheme has been declared, it can be refered to by its ID in any disclosures in the file. Each disclosure takes an optional list of certification scheme IDs, so that disclosures can refer to multiple certification schemes.

```toml
disclosures = [
	{ doc_type="annual-report",
	  url="https://example.com/impact-report-2024-2025.pdf",
	  title="Bcorp impact report for 2024-2025",
	  certification_schemes=["b-corp"]
	},
]

```

The validity period of a certification is captured by the existing valid_until property of a certificate disclosure.


```toml
disclosures = [
	{ doc_type="certificate",
	  url="https://example.com/bcorp-certificate-2026.pdf",
	  title="Bcorp certificate for 2026",
	  certification_schemes=["b-corp"],
      valid_until=2026-12-31
	},
]

```

## Consequences

This decision allows us to express all the required details about certification schemes within carbon.txt, and ensures that there's a single canonical entry in each carbon.txt file that refers to that specific certification scheme. It also allows for  richer structure about disclosures to be inferred (eg "this particular disclosure provides evidence for this particular commitment, required as part of a particular certification scheme"). In addition, downstream users are able to see at a glance what certification schemes a site or organization subscribes to, and do useful things based on that, such as display a logo. In addition, we don't need to maintain a list of recognised certification scheme identifiers, these are declared within the scope of the file, and the URL of the certifying organisation provides a global identifier

### What's out of scope (for now)

A few subtleties were raised in the [discussion that led to this decision](https://github.com/thegreenwebfoundation/carbon.txt/issues/31) that we have deferred adressing until a later version - we consider that they do not prevent a useful first version of this functionality from being released, and won't lead to difficult breaking changes in the future. These are:

 - The ability to differentiate between the overall validity period of an organization's membership of a scheme, and a requirement to periodically be re-assesed within it (eg, for B.Corp a certification lasts 5 years with annual renewals)
 - The ability to specify that a particular certification applies only to a particular region or organizational unit.
