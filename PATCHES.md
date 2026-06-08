# Candidate Patches

> **Static review only.** These diffs were authored and reviewed by
> independent agents reading source. They were NOT compiled, run, or
> re-attacked. Read each diff yourself before applying — see
> `docs/patching.md#reviewing-generated-patches` for what to look for.

**Input:** TRIAGE.json · **Repo:** /home/stefan/workspace/SecObserve/SecObserve · 11 findings → 11 diffs

---

## bug_00: [HIGH] Issue-tracker API key returned in product API responses to any user with read (View) permission  (f001)

`backend/application/core/api/serializers_product.py:295` · sensitive-data-exposure · owner: ?
**Status:** static_review_only · review ACCEPT · style 8/10
**Diff:** `PATCHES/bug_00/patch.diff` (2 hunks, 36 lines)

**Rationale:** Root cause is `ProductCoreSerializer.to_representation` at serializers_product.py:123. It serializes every model field and never masks `issue_tracker_api_key`. The fix pops it from output unless the caller holds `Permissions.Product_Edit`, reusing the permissions value the serializer already computes. Mirrors the existing `ApiConfigurationSerializer.to_representation` precedent. Placed in the base class to fix both `ProductSerializer` and `ProductListSerializer` at one inheritance point.

**Variants checked:** ProductCoreSerializer.to_representation (base, fix site), ProductSerializer.Meta, ProductListSerializer.Meta — all resolve to the single inherited to_representation. NestedProductSerializer does NOT inherit this base and still emits the key — flagged as a separate follow-up finding.

**Bypass considered:** Tried reaching the key through ProductListSerializer (inherits the same base, pop applies). Tried Reader spoofing the gate: permissions are computed server-side from the user's actual role, not client input. Residual path: NestedProductSerializer (embedded in API-configuration/member responses) is a distinct sink outside f001's scope.

---

## bug_01: [MEDIUM] Issue-tracker API key stored unencrypted while siblings use EncryptedCharField  (f002)

`backend/application/core/models.py:101` · sensitive-data-exposure · owner: ?
**Status:** static_review_only · review ACCEPT · style 9/10
**Diff:** `PATCHES/bug_01/patch.diff` (4 hunks, 88 lines)

**Rationale:** Converts `issue_tracker_api_key` from plain CharField to EncryptedCharField, mirroring the established repo pattern at `import_observations/models.py:44` and `access_control/models.py:104`. Includes a data migration to re-encrypt existing plaintext rows and a regression test.

**Variants checked:** Checked all EncryptedCharField usages in the repo (JWT_Secret.secret, Api_Configuration.api_key, basic_auth_password). Also checked `issue_tracker_username` — left as CharField since it carries usernames not credentials.

**Bypass considered:** Verified that the migration correctly chains from the latest migration (0086) and that the re-encryption RunPython handles both empty and populated fields.

---

## bug_02: [MEDIUM] Committed default DJANGO_SECRET_KEY in shipped prod compose  (f006)

`docker-compose-prod-postgres.yml:85` · hardcoded-secret · owner: ?
**Status:** static_review_only · review ACCEPT · style 8/10
**Diff:** `PATCHES/bug_02/patch.diff` (1 hunk, 11 lines)

**Rationale:** Replaces `${SO_DJANGO_SECRET_KEY:-NxYPEF5l...}` with `${SO_DJANGO_SECRET_KEY:?...}` — the fail-closed Compose form that aborts startup if the variable is unset. Removes the embedded secret at its root.

**Variants checked:** Same pattern exists in docker-compose-prod-mysql.yml:85 and docker-compose-prod-test.yml:52 — scoped to the specific file cited in the finding.

**Bypass considered:** Verified that no in-code fallback in settings/base.py would reinstate a default; SECRET_KEY = env("DJANGO_SECRET_KEY") has no fallback.

---

## bug_04: [MEDIUM] Stored XSS via SBOM component names assigned to element.innerHTML  (f008)

`frontend/src/core/observations/Mermaid_Dependencies.tsx:111` · xss · owner: ?
**Status:** static_review_only · review ACCEPT · style 9/10
**Diff:** `PATCHES/bug_04/patch.diff` (2 hunks, 19 lines)

**Rationale:** Replaces `element.innerHTML` with `element.textContent` at line 111, eliminating the HTML parsing sink. Adds `securityLevel: 'strict'` to `mermaid.initialize` as defense-in-depth. `textContent` is how mermaid is intended to be used — it reads the text content of the element and renders SVG itself.

**Variants checked:** No other innerHTML assignments found in the frontend source. The JSX children of the `<a>` element in the same component use React's auto-escaping (safe).

**Bypass considered:** Checked whether diagram syntax injection could bypass mermaid's own sanitizer — `securityLevel: 'strict'` blocks script/click bindings in diagram syntax, covering that vector too.

---

## bug_05: [MEDIUM] mark_as_viewed unscoped lookup allows cross-product notification existence probing  (f015)

`backend/application/notifications/api/views.py:67` · idor · owner: ?
**Status:** static_review_only · review ACCEPT · style 9/10
**Diff:** `PATCHES/bug_05/patch.diff` (3 hunks, 51 lines)

**Rationale:** Replaces `get_notification_by_id(pk)` (unscoped `Notification.objects.get`) with `self.get_object()`, which routes through `get_queryset()` → `get_notifications()` (membership-scoped). Out-of-scope pks now yield 404 via DRF's standard authorization path. Drops the now-unused import.

**Variants checked:** Checked all uses of `get_notification_by_id` — only used in mark_as_viewed. The bulk notification path uses a different scoping mechanism. `get_notifications()` is used by get_queryset for list/retrieve and is the correct scoping function.

**Bypass considered:** Verified that self.get_object() triggers `UserHasNotificationPermission.has_object_permission`, which was previously bypassed because the custom action never called get_object().

---

## bug_06: [MEDIUM] OIDC username claim trusted as local-account key -> account takeover  (f018)

`backend/application/access_control/services/oidc_authentication.py:79` · auth-bypass · owner: ?
**Status:** static_review_only · review ACCEPT · style 9/10
**Diff:** `PATCHES/bug_06/patch.diff` (1 hunk, 15 lines)

**Rationale:** Inserts an `is_oidc_user` gate at line 83, immediately after `get_user_by_username` and before `_check_user_change`. Rejects the collision with `AuthenticationFailed` before any mutation. The check uses a server-controlled DB column, not a token-derived value.

**Variants checked:** `_create_user` path is unreachable here because get_user_by_username already returned a user. No other OIDC authentication paths exist.

**Bypass considered:** Checked whether `is_oidc_user` could be set via API — it is a server-side DB field not exposed in any serializer's writable fields. An attacker cannot spoof it.

---

## bug_07: [LOW] Approval gate bypass via In-review status carrying severity/VEX downgrade  (f009)

`backend/application/core/services/assessment.py:65` · broken-access-control · owner: ?
**Status:** static_review_only · review ACCEPT · style 8/10
**Diff:** `PATCHES/bug_07/patch.diff` (1 hunk, 21 lines)

**Rationale:** Fixes the approval gate by computing whether non-status fields changed independently from the IN_REVIEW exemption. Any severity/priority/vex change now forces NEEDS_APPROVAL even when bundled with an IN_REVIEW status transition.

**Variants checked:** Same save_assessment function is called from both the single assessment endpoint (views_observation.py:148) and the bulk path (observations_bulk_actions.py:41/94) — the fix covers both.

**Bypass considered:** Checked whether status-only changes still bypass approval (they should, per design) — confirmed the fix preserves the IN_REVIEW exemption when status is the only change.

---

## bug_08: [LOW] JSON breakout in Slack/Teams notifications via backslash in import-derived title  (f013)

`backend/application/notifications/services/send_notifications_base.py:43` · template-injection · owner: ?
**Status:** static_review_only · review ACCEPT · style 8/10
**Diff:** `PATCHES/bug_08/patch.diff` (16 hunks, 270 lines)

**Rationale:** Replaces hand-built JSON templates with Python dict construction + `json.dumps()`. Eliminates the HTML-escape/JSON-escape parity bug entirely by never mixing the two escaping contexts. Covers both Teams and Slack notification paths.

**Variants checked:** Both send_msteams_notification and send_slack_notification paths fixed. Also checked exception notification paths (send_exception_msteams_notification/slack) — same pattern applied. Template files (.tpl) replaced with dict-based construction.

**Bypass considered:** Verified that json.dumps handles all special characters (backslash, quotes, control chars) correctly per RFC 8259. No HTML escaping involved in the new path.

---

## bug_09: [LOW] XLSX export writes attacker fields into cells without formula-escaping  (f019)

`backend/application/commons/services/export.py:47` · csv-injection · owner: ?
**Status:** static_review_only · review ACCEPT · style 7/10
**Diff:** `PATCHES/bug_09/patch.diff` (2 hunks, 24 lines)

**Rationale:** Adds a formula-escaping helper that prefixes leading `= + - @ \t \r` with a single quote in string cells, matching what defusedcsv does for CSV. Applied to both header and value writes in export_excel.

**Variants checked:** export_csv already uses defusedcsv (line 63). export_excel was the only unprotected path.

**Bypass considered:** Checked whether non-string cell types (numbers, dates) could carry formula triggers — the helper only processes string values, which is correct since formula triggers are string-level.

---

## bug_10: [LOW] Teams/Slack webhook URL user-controlled, weak host validation (blind SSRF)  (f020)

`backend/application/notifications/services/send_notifications_base.py:45` · ssrf · owner: ?
**Status:** static_review_only · review ACCEPT · style 8/10
**Diff:** `PATCHES/bug_10/patch.diff` (7 hunks, 136 lines)

**Rationale:** Adds `_validate_webhook_url` helper that enforces HTTPS, resolves the host via `socket.getaddrinfo`, and rejects private/loopback/link-local/reserved/multicast/unspecified IP addresses. Adds `allow_redirects=False` to block redirect-based bypass. Applied to both Teams and Slack notification paths.

**Variants checked:** Both product-level webhooks (via serializer validation) and global Settings webhooks (via send_notifications_base) now pass through the validator. Exception notification paths also covered.

**Bypass considered:** Residual TOCTOU/DNS-rebinding gap (validated IP not pinned for actual request) is noted as a hardening limitation, not a regression — the patch is strictly an improvement over the prior state of zero validation.

---

## bug_03: [MEDIUM] Committed default FIELD_ENCRYPTION_KEY defeats at-rest field encryption  (f007)

`docker-compose-prod-postgres.yml:86` · hardcoded-secret · owner: ?
**Status:** static_review_only · review REJECT · style 5/10
**Diff:** `PATCHES/bug_03/patch.diff` (5 hunks, 94 lines)

**Rationale:** Replaces the FIELD_ENCRYPTION_KEY fallback with fail-closed `:?` form and adds a burned-key check in settings/base.py.

**Variants checked:** Same default exists in docker-compose-prod-mysql.yml:86 and docker-compose-prod-test.yml:53.

**Bypass considered:** The burned-key check detects the exact committed key at boot time.

> **Rejected by reviewer:** Core approach correct but incomplete: only patches one of several compose files shipping same default, and burned-key check breaks test/CI infrastructure that still uses that key (docker/backend/unittests/envs/django:15, docker-compose-unittests.yml:20, run_pylint.sh:19, run_mypy.sh:19).

---

## Skipped

None.
