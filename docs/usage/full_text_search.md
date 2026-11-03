# Full text search

The full text search finds observations by parts of their texts, including the comments of their observation log. It complements the filter for the title, which searches only in the title of the observations.

!!! note
    The full text search is only available if SecObserve uses a PostgreSQL database. With MySQL, the field is not shown and the REST API rejects the filter.

## Where to search

The field **Full text search** is shown in the filter bar of

* the list of all observations,
* the observations tab of a product,
* the observations tab of a product group,
* the lists of observations to be reviewed, in the menu **Reviews** and in the reviews tab of a product,
* the observations of a component.

It can be combined with all other filters, e.g. to search only in observations with a specific severity or status.

## Searched texts

The search looks into these texts of an observation:

* Title
* Description
* Vulnerability id
* Vulnerability id aliases
* Origins: Component name and version, Docker image name and tag, endpoint URL, source file, cloud resource and Kubernetes resource
* Comments of the entries in the observation log, e.g. the comments of assessments

Comments written automatically by SecObserve are not searched, because they would match nearly every observation. These are the comments written by parsers during imports, by rules and VEX statements and when they are removed, when an observation has been created or changed manually and when a risk acceptance has expired.

## Matching rules

* The words of the input are searched separately and all of them must be found, in any order. Each word can be in any of the texts or comments: `injection accepted` finds an observation with `injection` in its description and `accepted` in an assessment comment.
* A word without double quotes is found anywhere in the texts, also as part of a longer word: `jection` finds `injection`, `sql` finds `mysql` and `CVE-2021-44` finds `CVE-2021-44228`.
* A word in double quotes is only found as a whole word: `"sql"` finds `SQL injection`, but not `mysql`. Only the characters directly before and after the found text are checked: they must not be a letter, a digit or an underscore. All other characters, like hyphens, dots or slashes, separate words. Therefore `"CVE-2021"` finds `CVE-2021-44228` (followed by `-`) and `"log4j"` finds `org.apache.log4j.core`, but `"CVE-2021-4422"` doesn't find `CVE-2021-44228` (followed by `8`).
* Several words in double quotes are searched as a phrase: `"sql injection"` finds `SQL injection` with exactly one space between the words, but not `injection in SQL`.
* The search is case-insensitive: `STORED "xss"` finds `Stored XSS`.
* There are no other operators: `or` and `-` are searched like all other characters. A double quote without a closing one is ignored.
* Words with fewer than 3 characters are ignored, also in double quotes, because they cannot be searched efficiently. If all words are shorter, the full text search doesn't filter at all.
* At most 10 words are searched, all further words are ignored.

## REST API

The full text search is available as the query parameter `full_text_search` of the endpoint `/api/observations/`, see [REST API](../integrations/rest_api.md):

```
GET /api/observations/?full_text_search=%22sql%22%20injection
```

With a MySQL database, the request fails with status code `400` and the message `Full text search is only available with PostgreSQL`.
