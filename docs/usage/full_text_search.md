# Full text search

The full text search finds observations by parts of their texts, including the comments of their observation log. It complements the filter for the title, which searches only in the title of the observations.

!!! note
    The full text search is only available if SecObserve uses a PostgreSQL database and it has been activated, see [Activation](#activation). Otherwise the field is not shown and the REST API rejects the filter.

## Activation

The full text search is deactivated by default, because it needs additional indexes in the database. They take disk space and make writing observations and their logs a little slower. An administrator activates the full text search with a management command in the backend container, e.g. with Docker Compose:

```bash
docker compose exec backend python manage.py full_text_search activate
```

The command

* creates the PostgreSQL extension `pg_trgm`, if it doesn't exist yet. The database user of SecObserve needs the permission to create it. Since PostgreSQL 13, `pg_trgm` is a trusted extension, which can be created by every user with the `CREATE` privilege on the database, e.g. the owner of the database.
* creates the indexes for all [searched texts](#searched-texts). They are built without blocking SecObserve, but this can take a while with many observations.
* shows the field **Full text search** once all indexes have been created. Users who are already logged in see it after their next login.

If the command is interrupted, it can simply be started again. Indexes, that have not been built completely, are dropped and created again.

The full text search is deactivated with:

```bash
docker compose exec backend python manage.py full_text_search deactivate
```

The field is hidden first and then the indexes are dropped. The extension `pg_trgm` is kept.

The settings show in the features section whether the full text search is activated. It can only be changed with the management command.

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

Comments written automatically by SecObserve are not searched, because they would match nearly every observation. These are the comments written by parsers during imports, by rules and VEX statements and when they are removed, when an observation has been created or changed manually and when a risk acceptance has expired. One exception: If a rule has a description, it is used as the comment of the observation log. This comment is searched after the rule has been deleted, because it cannot be distinguished from a comment written by a user anymore.

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

If the full text search has not been activated, e.g. with a MySQL database, the request fails with status code `400` and the message `Full text search is not activated`.
