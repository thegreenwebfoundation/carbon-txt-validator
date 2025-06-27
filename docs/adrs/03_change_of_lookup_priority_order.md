# ADR 3: Changed order of lookup priority for carbon.txt resolutaion

## Status

Accepted

## Context

In [ADR 02](02_improvements_to_delegation_and_domain_validation.md), we defined the order of carbon.txt resolution as follows:

- Look for carbon.txt in the *root of the domain at `/carbon.txt`*. If it is not found:
- Look for carbon.txt in the *well-known directory at `/.well-known/carbon.txt`*. If it is not found:
- Look for a `carbon-txt-location` *DNS text record* for the domain. If none is present:
- Look for a `carbon-txt-location` *HTTP header* returned by the web server.

The idea here was to ensure that a more specific carbon.txt can always override a more general one, and to ensure that users always have some mechanism by which they can override a carbon.txt set by an upstream provider.

In addition, we don't continue *down* the lookup stack on any error that it's possible to encounter, as this would make debugging a carbon.txt implementation difficult. In particular, the carbon.txt file is "unreachable", and we continue down the lookup stack IFF:
     - The web server returns a status >= 400
     - There is a network error connecting to the web server.

By design, a carbon.txt that is present, but not parsable is not considered "unreachable", and in this case, instead, the lookup process stops and the error is surfaced to the user. This allows users to use the validator to debug their carbon.txt contents, which would not be possible were the validator to continue down the lookup stack and encounter another, well formed carbon.txt at another location.

This all works well in theory, but in practice, we've encountered an interesting problem. While testing the [linked domains](https://github.com/thegreenwebfoundation/admin-portal/pull/643) implementation in the GWF admin portal, we attempted to validate the domain `developers.thegreenwebfoundation.org`, using a DNS TXT record, which consistently failed with an "Invalid TOML" error.

On closer inspection this is because the web server (potentially via cloudflare) is configured to always render the documentation root with a 200 status when a page does not exist, rather than returning a 404, and this therefore produces an HTML page which we attempt to parse as TOML, resulting in a parse error. As discussed above, this prevents the validator continuing down the carbon.txt lookup stack, and the DNS TXT record is never found.

The `developers.thegreenwebfoundation.org` site is undoubtedly misconfigured (unfound pages should return a 404 error code): but in a way that appears to be beyond our control, and it seems reasonable to assume that we'll find similar edge cases out on the web in general, and among our customers specifically, therefore, it seems prudent to do something to address this.


## Decision

We have two options here which would allow a user to succesfully provide a carbon.txt location using DNS, in a case where there web server always returns a 200, even for URIs that don't exist:

1. We could make sure the carbon.txt finder ALWAYS continues down the lookup stack on errors until it's exhausted every possibility, regardless of the class of errors encountered (so that a carbon.txt that's "found" but contains invalid TOML would not be surfaced a an error and the next carbon.txt location tried instead)
2. We could move the DNS lookup to the *top* of the stack, so that it's always tried first, and provides an "escape hatch" to get around any weird HTTP server configurations that might cause problems.

After some discussion with @fershad and @mrchrisadams, we have decided to proceed with **Option 2** (changing the lookup order to give DNS priority) for now, for several reasons:

1. It more closely follows expectations of "how the web works": A DNS lookup is performed *before* a page is requested, typically, so it makes sense to mirror this here
2. It doesn't run the risk of swallowing errors that may be useful to our users in debugging their carbon.txt implementation
3. It's easier to explain and document: There are 4 possible carbon.txt locations which are tried in sequence, if any is not found, we move on to the next. We don't need to explain any confusing error semantics or special cases.
4. There are very few cases where a website owner would not have access to add a DNS record for their domain, but many where reconfiguring a webserver might not be possible. Allowing a DNS override of everything ensures that the owner of a domain can always control the claims they make in carbon.txt.


## Consequences

From now on, the order of lookups used in the carbon.txt finder will be as follows:

- Look for a `carbon-txt-location` *DNS text record* for the domain. If none is present:
- Look for carbon.txt in the *root of the domain at `/carbon.txt`*. If it is not found:
- Look for carbon.txt in the *well-known directory at `/.well-known/carbon.txt`*. If it is not found:
- Look for a `carbon-txt-location` *HTTP header* returned by the web server.
