# ADR 4: On the www. subdomain and "going our own way" on domain delegation.

## Status

Accepted


## Context

In [ADR 02](02_improvements_to_delegation_and_domain_validation.md), we set out the following reasons for **NOT** following HTTP redirects (301 or 302) when looking up carbon.txts for a domain:


> We explicitly *do not* follow HTTP 301 or 302 redirects when locating a carbon.txt file, preferring instead the use of the CarbonTxt-Location Header or the carbon-txt-location DNS TXT field. This is for two reasons:
>
> Firstly, following redirects transparently allows abuse of the service whereby `bad-polluting-company.com` could redirect their carbon.txt to `good-green-company.com`'s carbon.txt URL, without the passing-off being explicitly flagged to the user'. Using our own delegation mechanisms allows a way for consumers to follow these types of redirections while surfacing the fact that the delegation is happening in a transparent manner.
>
> Secondly, following HTTP redirects would complicate the priority order above considerably (should redirects be followed before or after the CarbonTxt HTTP header or dns record? What if a 301 response _also_ contains the carbon.txt header?) We haven't found a satisfactory answer for any of these cases, nor a particulary compelling use-case for following HTTP redirects, while the other mechanisms exist.
>
> This both makes the behaviour of the validator more predictable, and allows flexibility in overriding the published carbon.txt in specific contexts.

However, in implementing the carbon.txt based domain linking functionality in the Green Web Platform, and in user testing it, we came across a specific case that runs counter to expectations, and can be hard to debug - the case of the `www.` subdomain, which is frequently [either blanket 301 redirected to the TLD](https://no-www.org/), or [vice versa](https://web.archive.org/web/20220527025758/https://www.yes-www.org/why-use-www/).

This frequently tripped us up when trying to set up domain delegation, or when validating primary domains. If `example.com` has set up a blanket redirect to `www.example.com`, and we check `example.com`, the check will fail as will checks for any other domains that link to it (And vice versa).

We arrived at two options to deal with this:

1. backtrack on our earlier decision, and follow redirects after all
2. somehow make the `www.` subdomain an explicit special case.

Option 2 (Making the `www.` subdomain a special case) feels a little hacky, and perhaps more difficult to communicate to carbon.txt users, but after some discussion we've decided it's the better course of action for two reasons:

1. For the reason described above: We actively want to ensure that carbon.txt delegations are NOT transparently followed in the browser, as with HTTP redirects, so that users can be sure of the provenance and / or existence of any given carbon.txt file.
2. Arbitrarily following HTTP redirects means following them transitively - including arbitrarily long chains, and even infinite loops. This is a performance concern, as we  need carbon.txt lookups to resolve quickly (for instance, in the Green Web Check Tool, the volume of requests means that a carbon.txt lookup must take less than 1s as an absolute maximum). Special casing the `www.` subdomain ensures that in the worst case, only two domains need to be checked.
3. Following both HTTP redirects AND our "CarbonTxt-Location" HTTP header introduces the possibility of ambiguity or contradictory information in the same request. We'd need to settle on a priority order for following these mechanisms, which would be somewhat arbitrary, and also a source of unneeded complexity.

## Decision

When resolving the carbon.tst for a domain, in the case that the requested domain is a TLD or a www. subdomain:

- The domain requested is attempted FULLY (be it TLD or `www.`)
- Only if NO lookup mechanism succeeds do we then try the alternate domain (`www.` or TLD respectively)
- We signal that this is happening in the logs.

All other subdomains (including `www.` subdomains of subdomains) are treated exactly as in the previous behaviour, and no alternate domain is looked up.

We continue NOT to follow HTTP redirects, for the reasons set out in [ADR 02](02_improvements_to_delegation_and_domain_validation.md), as well as the risk of infinite redirect loops, or unmanageably long chains of redirects, detailed above.

This logic should be followed ONLY for domain lookups, not file or URL lookups, following the same logic set out for all delegation mechanisms in [ADR 02](02_improvements_to_delegation_and_domain_validation.md).

However, we note this type of special case is probably not a precedent we want to set: there's a risk that if we encountered other "common situations" like this that we haven't considered, and which could be special cased for similar reasons - then we would end up with an explosion of complexity, and a carbon.txt resolution process which is opaque, and difficult to reason about and explain. Therefore, in the event that we find we have to deal with other unforseen consequence of not following HTTP redirection, that we will reconsider this decision before adding any more special cases.


## Consequences

**What becomes easier or more difficult to do because of this change?**

Advantages:
- Implementing carbon.txt on the most common configurations of `www.` subdomains "just works", transparently.
- We continue to guard against "passing-off" carbon.txt using HTTP redirects in order to falsely assert someone else's green claims
- We limit the number of HTTP requests needed to look up carbon.txt for a given domain, rather than folllowing arbitrarily long redirect chains.
- We've explicitly committed not to allow this to become precedent for proliferating special cases, and to revisit this decision if more common redirect patterns that cause problems arise.

Disadvantages:

- The addition of a special case for `www.` subdomains makes it more difficult to reason about, document and explain the carbon.txt resolution process.
- The number of requests needed to resolve a carbon.txt for a domain, in the worst case, is now double what it was before. We should keep an eye on the performance implications of this in downstream uses of the validator.
