# ADR 2: Improved architecture for domain validation and carbon.txt delegation

## Status

Accepted

## Context

While in the process of developing the Green Web Directory domain validation system, and simultaneously aiding some friendly hosting providers to produce and publish their own carbon.txt files, we've come across a couple of wrinkles in the HTTP Via and DNS delegation mechanism which we'd previously designed.

The first is that placing the domain hash in the DNS TXT record or HTTP Via header works great for validating domains  which delegate carbon.txt to another domain, but does not allow us any mechanism for validating the "canonical" domain where the carbon.txt is hosted. The presence of the carbon.txt is not enough, as that would mean I could take control of any domain which already has a carbon.txt simply by making a validation claim on it.

The second is that our expectations of how the HTTP Via header might be used and formatted go slightly against what's permitted by the [HTTP 1.1 spec](https://datatracker.ietf.org/doc/html/rfc2616#section-14.45), and some quite common existing real-world usage of it - particularly Amazon Cloudfront, which has caused issues for hosting providers.

In brief, the Via header doesn't require the presence of an actual HTTP URL, a "pseudonym" can be used instead, and the "field" we use for the domain hash is a space for comments, which could be anything:

```
Via: [<protocol-name>/]<protocol-version> <pseudonym>|<url> [comment]
```

This leads to problems with (existing) Via headers which use a pseudonym instead of a URL, or have a comment which does not look like a GWF domain hash, as the validator fails. In addition, this failure happens if the header is present even when directly requesting an (existing, valid) carbon.txt file, rather than looking up the domain generally. This causes confusion for providers attempting to set up their carbon.txt for the first time, as valid carbon.txt files are reported as invalid, and potentially leads to them abandoning the process.

## Decision

The main change proposed here is to separate out the business of _delegating_ the location of carbon.txt to another domain from the business of verifying ownership of a domain in the Green Web platform. In the current carbon.txt design, a single HTTP Via header or DNS TXT record does double duty here, representing both the canonical carbon.txt location and asserting ownership of the domain via a domain hash.

Instead we propose that this should be done by either two separate HTTP headers:

```
CarbonTxt-Location: https://example.com/carbon.txt
GWF-DomainHash: <domain hash>
```

... or two separate DNS TXT records:

```
carbon-txt-location: https://example.com/carbon.txt
gwf-domain-hash: <domain hash>
```

(there's also no reason why clients should not mix and match - using a DNS record to show domain ownership, for instance, and an HTTP header for carbon.txt location or vice-versa). The current `carbon-txt` TXT record and `Via` Header delegation methods will be deprecated (however, we have no evidence they're actually being used "in the wild" yet, ).

We prefix the DomainHash HTTP header with GWF to make it clear it's a non-standard header of use only by our organization, while we do not prefix the CarbonTxt header in the same way, to make it clear that it's part of a potential future standard, as recommended in [RFC 6648](https://datatracker.ietf.org/doc/html/rfc6648).

This provide the same functionality to end users (the ability to delegate carbon.txt to another location either vis DNS or HTTP, as well as the ability to assert ownership of a domain in the GWF platform), but in a manner which better respects existing standards and usage, and clearly separates out the general concerns of publishing and discovering carbon.txt files (the object of this standard) from details which are specific to our concerns as the Green Web foundation (verifying control of domains by GWF providers).

In addition, we also propose elaborating a few further details around how the delegation mechanism behaves, so that the behaviour of the validator can be more easily reasoned about and documented. These are as follows:

We should standardise and make explicit a priority order for the delegation mechanisms we offer:
    - A carbon.txt in the root of the domain should always take priority over
    - a carbon.txt in the `well-known` directory, which should always take priority over
    - a DNS TXT record, which should always take priority over
    - an HTTP header.

We explicitly *do not* follow HTTP 301 or 302 redirects when locating a carbon.txt file, preferring instead the use of the CarbonTxt-Location Header or the carbon-txt-location DNS TXT field. This is for two reasons: Firstly, following redirects transparently allows abuse of the service whereby `bad-polluting-company.com` could redirect their carbon.txt to `good-green-company.com`'s carbon.txt URL, without the passing-off being explicitly flagged to the user'. Using our own delegation mechanisms allows a way for consumers to follow these types of redirections while surfacing the fact that the delegation is happening in a transparent manner. Secondly, following HTTP redirects would complicate the priority order above considerably (should redirects be followed before or after the CarbonTxt HTTP header or dns record? What if a 301 response _also_ contains the carbon.txt header?) We haven't found a satisfactory answer for any of these cases, nor a particulary compelling use-case for following HTTP redirects, while the other mechanisms exist.

This both makes the behaviour of the validator more predictable, and allows flexibility in overriding the published carbon.txt in specific contexts.

The DNS TXT record and HTTP Header validation mechanisms should allow users to delegate EITHER to a full URL of a carbon.txt OR to another domain. In the latter case, the same resolution mechanism will be applied recursively to the new domain, until a concrete carbon.txt file is
One consequence of this is that the validator _should never_  follow any of the delegating logic when testing full URLs that directly reference a carbon.txt file with the `/api/validate/url/` endpoint. This is both consistent with the logic above (a local URL with a carbon.txt file always takes priority over a delegation mechanism), but also solves a concrete problem we have currently where hosting providers attempting to publish and validate their carbon.txt files are running into spurious errors because of http headers inserted by downstream CDNS outside of their control. A change making sure that this is the case is [already implemented in #84](https://github.com/thegreenwebfoundation/carbon-txt-validator/pull/84).

## Consequences

**What becomes easier or more difficult to do because of this change?**

Some advantages of this change:

 - The behaviour of the validator becomes easier to reason about as we have made the order of priority of delegation mechanisms explicit.
 - It becomes easier to test the "simplest" case -  a carbon.txt file directly hosted on a domain, as no HTTP headers or DNS records can override it.
 - We are able to provide a mechanism whereby GWF validators can validate control over all their domains (including the canonical domain hosting their carbon.txt file), while maintaining a separation of concerns between this and the carbon.txt standard itself.
 - We avoid issues arising from other uses of the HTTP Via header, and make our own implementation more "standards-friendly" by not overloading an existing standard and widely-used header with our own non-standard semantics.
 - We allow for other means of validating domain ownership in the GWF platform, including manual overrides by GWF staff (useful in the case of large, trusted, providers who might want to provide us with a list of controlled domains directly), or the future addition of, for instance, a domain-hash.txt file in the .well-known directory.
 - We delineate a separation between the business of the carbon.txt standard (discoverability and publishing of sustainability data), and the role of the GWF (aggregating this data and providing an additional layer of trust and verification on top of it). This also makes it easier for other actors to provide similar trust services on top of the carbon.txt standard in future as part of a broader carbon.txt ecosystem.
 - We defer any broader work on trust and verification in the carbon.txt ecosystem until we have time to tackle it properly, and come up with a good solution: We've discussed something similar to ACME protocol (the existing GWF domain hash implementation is broadly similar to ACME's DNS-1 challenge), but haven't yet worked through the details of how it might be incorporated into carbon.txt. By making the decision to rule the current domain-hash implementation out of scope for now, we open up the possibility of returning to the issue later with more focused attention and coming up with a better implementation, rather than committing ourselves early to an approach which may not be optimal.


Some possible disadvantages:

- This might introduce a little additional complexity for GWF-verified hosting providers, as they would need to create two additional DNS TXT records (or add two HTTP headers) instead of one in order to set up their provider to use carbon.txt. However, given that we are in control of the design of this process in the greenweb platform, we're confident that we can mitigate this.
- It adds a requirement for substantially more detail in the documentation, but we think that the effect of this will be greater clarity rather than greater confusion.
- If, in the future, we decided we wanted to build a decentralised trust/verification mechanism into the carbon.txt standard itself (using something analogous to OpenID connect or TLS chains of trust), the separation between the two headers or txt records would become superfluous, and perhaps should be rethought. This isn't on our roadmap though, so isn't really a concern for now.
