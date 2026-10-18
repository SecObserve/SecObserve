# Full text search

The full text search finds observations by words in their texts, including the comments of their observation log. It complements the filter for the title, which searches only in the title of the observations.

!!! note
    The full text search is only available if SecObserve uses a PostgreSQL database. With MySQL, the field is not shown and the REST API rejects the filter.

## Where to search

The field **Full text search** is shown in the filter bar of

* the list of all observations,
* the observations tab of a product,
* the observations tab of a product group.

It can be combined with all other filters, e.g. to search only in observations with a specific severity or status.

## Searched texts

The search looks into these texts of an observation:

* Title
* Description
* Recommendation
* Vulnerability id
* Vulnerability id aliases
* Comments of all entries in the observation log, e.g. the comments of assessments

An observation is found if either its own texts or one of its observation log comments match the whole search query. Words are not combined across them: searching for `injection accepted` doesn't find an observation that has `injection` only in its description and `accepted` only in a comment of its observation log.

## Search syntax

The search uses the web search syntax of PostgreSQL, which is similar to the syntax of common web search engines:

| Input | Finds observations ... |
|-------|------------------------|
| `sql injection` | ... containing both words, in any order |
| `"sql injection"` | ... containing both words next to each other, in this order |
| `xss or csrf` | ... containing at least one of the words |
| `injection -sql` | ... containing `injection`, but not `sql` |

All elements can be combined, e.g. `"sql injection" or xss -test`.

## Matching rules

* The search is case-insensitive: `STORED xss` finds `Stored XSS`.
* Every word of the query is matched as the beginning of a word in the texts: `inject` finds `injection` and `injected`. This applies inside quotes as well (`"sql inj"` finds `SQL injection`) and to excluded words (`-xss` excludes texts with `XSS-attack`).
* Parts in the middle or at the end of a word are not found: `jection` doesn't find `injection` and `sql` doesn't find `mysql`.
* Words containing hyphens are found as a whole and as their beginning: `CVE-2021-44228` and `CVE-2021-44` both find `CVE-2021-44228`.
* The words are not reduced to their stem and there are no stop words, so the search works in the same way for texts in all languages.

## REST API

The full text search is available as the query parameter `full_text_search` of the endpoint `/api/observations/`, see [REST API](../integrations/rest_api.md):

```
GET /api/observations/?full_text_search=%22sql%20injection%22%20-test
```

With a MySQL database, the request fails with status code `400` and the message `Full text search is only available with PostgreSQL`.
