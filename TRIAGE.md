# Triage Report

30 in -> 1 duplicate, 18 false positives, 11 confirmed (1 high / 6 medium / 4 low), 1 needs manual test

Context: interactive; environment = Internet-facing web service (Django/DRF API); scoring = Derived HIGH/MEDIUM/LOW; 3-vote verification.

## Act on these

### [HIGH] Issue-tracker API key returned in product API responses to any user with read (View) permission  (f001)
`backend/application/core/api/serializers_product.py:295` | sensitive-data-exposure | claimed HIGH (alignment +1) | confidence 0.9/10
**Owner:** component: backend/core/api/; top committer Stefan Fleckenstein (43/44 recent commits); no CODEOWNERS
**Verdict:** exploitable, votes TP=3 FP=0 CV=0
**Preconditions (4):**
  - Attacker is authenticated (valid session/token; endpoint enforces IsAuthenticated, anonymous is rejected)
  - Attacker holds at least the lowest Reader role on the target product, granting object-level Product_View via membership (UserHasProductPermission.has_object_permission -> check_object_permission with get_permission=Permissions.Product_View)
  - An issue_tracker_api_key is actually configured (non-empty) on that product; the field is a blank-allowed CharField, so a product with no issue-tracker integration has no secret to leak
  - Attacker issues GET /api/products/{id}/ for a product they can view (ProductViewSet retrieve uses ProductSerializer whose Meta.exclude omits issue_tracker_api_key, with no write_only/to_representation masking)
**Threat-model match:** Compliance-scoped data exposure (integration secrets / crypto keys): the product's Jira/GitHub/GitLab issue_tracker_api_...
**Why:** Confirmed by reading source, not the description. serializers_product.py:295 ProductSerializer.Meta uses exclude=["is_product_group","members","authorization_group_members","observation_notification_statuses"] and inherits fields="__all__" from ProductCoreSerializer (line 70). models.py:101 defines issue_tracker_api_key = CharField(max_length=255, blank=True) in cleartext, and it is NOT in any exclude list and has no write_only declaration. No to_representation override pops it: ProductCoreSerializer.to_representation (lines 123-129) only sets observation_notification_status_list; the api_key 

Confirmed in source: serializers_product.py:295 ProductSerializer.Meta uses exclude=[is_product_group, members, authorization_group_members, observation_notification_statuses] which does NOT exclude issue_tracker_api_key (models.py:101, a CharField). No write_only and no to_representation masking; the only handling of the field (lines 385/390) is write-time validation. ProductViewSet (views_produc
**Reachability evidence:** `backend/application/core/api/views_product.py:143`

### [MEDIUM] Stored XSS via SBOM component names assigned to element.innerHTML before mermaid sanitization  (f008)
`frontend/src/core/observations/Mermaid_Dependencies.tsx:111` | xss | claimed HIGH (alignment +1) | confidence 0.9/10
**Owner:** component: frontend/core/observations/; top committer Stefan Fleckenstein (7/10 recent commits); no CODEOWNERS
**Verdict:** mitigated, votes TP=2 FP=1 CV=0
**Preconditions (5):**
  - Attacker holds an authenticated account with at least Upload/Writer role on a product (low-priv, but explicitly an available role per the threat model).
  - Attacker uploads a crafted CycloneDX SBOM (or OSV report) whose component name / bom-ref contains an HTML payload, e.g. a component named '<img src=x onerror=...>'. The CycloneDX parser concatenates these names verbatim into origin_component_dependencies as 'A --> B' lines (cyclone_dx/parser.py:259, dependencies.py:24) with no escaping.
  - A victim opens the observation detail view and the 'Component dependency graph' is rendered (ObservationShowOrigins.tsx:94 -> MermaidDependencies useEffect), where element.innerHTML = createMermaidGraph(dependencies) (line 111) parses the attacker markup before mermaid.run(). No DOMPurify; component names are interpolated raw at lines 83-84.
  - For privilege-escalation/tenant impact the rendering victim must be a higher-privileged user (Maintainer/Owner) with access to the attacker's product; SecObserve scopes observations per product, so a cross-product victim must already have access to the attacker-controlled product.
  - MITIGATING: a browser that enforces the app's Content-Security-Policy will not run the inline onerror handler. backend/config/settings/base.py:277 sets script-src 'self' with NO 'unsafe-inline', which per CSP spec blocks inline event-handler execution (the <img onerror> PoC). Exploitation requires that this CSP NOT reach the React SPA document (the middleware applies to Django responses; the SPA is served separately), or an alternate non-inline-script vector.
**Threat-model match:** Privilege escalation to admin (and secondarily tenant-to-tenant data leakage): a low-priv Upload/Writer plants a stored-...
**Why:** Confirmed at Mermaid_Dependencies.tsx:111: `element.innerHTML = createMermaidGraph(dependencies)` executes BEFORE `mermaid.run()` at :112. createMermaidGraph (lines 73,83,84) embeds component names raw into the string with zero HTML escaping (wrapped as `id1("name")` and emitted as raw dependency lines). innerHTML assignment makes the browser HTML-parse the string at assignment time, so a component name like `<img src=x onerror=...>` fires onerror immediately, independent of mermaid strict-mode sanitization (which only governs mermaid's own rendered SVG output, not the pre-assignment parse).

Sink and source are statically confirmed: SBOM component names from untrusted uploads flow unescaped into element.innerHTML at Mermaid_Dependencies.tsx:111, parsed before mermaid.run() and with no DOMPurify, so the markup is injected verbatim. Precondition column: this is authenticated stored XSS requiring an Upload/Writer account plus a victim render -> 2 attacker-side preconditions = MEDIUM band
**Reachability evidence:** `frontend/src/core/observations/ObservationShowOrigins.tsx:94`

### [MEDIUM] Committed default DJANGO_SECRET_KEY in shipped prod compose files  (f006)
`docker-compose-prod-postgres.yml:85` | hardcoded-secret | claimed HIGH (alignment -1) | confidence 0.9/10
**Owner:** component: deploy/compose; top committer Stefan Fleckenstein (28/50 recent commits); no CODEOWNERS
**Verdict:** needs_manual_test, votes TP=2 FP=1 CV=0
**Preconditions (5):**
  - Operator deploys using this compose file WITHOUT overriding SO_DJANGO_SECRET_KEY, so the committed literal NxYPEF5l... becomes the effective Django SECRET_KEY (config/settings/base.py:29 reads DJANGO_SECRET_KEY with no fallback, so the value comes from the compose default).
  - Attacker obtains the committed literal — trivially satisfied for a public repo, but still a distinct precondition.
  - The deployment relies on a SECRET_KEY-signed mechanism that an attacker can leverage: Django session cookies, signed cookies, or password-reset token generator. Primary API auth is JWT signed by a separate DB-stored random JWT_Secret (jwt_authentication.py:31/69, HS256), so forging JWTs is NOT possible via this key.
  - Attacker has network reach to the web endpoint that consumes the forged session cookie / reset token and a target account whose session or reset flow can be forged.
  - Integration secrets / crypto keys are NOT in scope of this key — they are protected by the separate FIELD_ENCRYPTION_KEY (base.py:432), so the compliance-scoped-data-exposure threat does not apply to SECRET_KEY.
**Threat-model match:** Partial: maps to "Privilege escalation to admin" only if session cookies / password-reset tokens are the live auth path ...
**Why:** Verified the finding directly. docker-compose-prod-postgres.yml:85 ships DJANGO_SECRET_KEY: ${SO_DJANGO_SECRET_KEY:-NxYPEF5lNGgk3yonndjSbwP77uNJxOvfKTjF5aVBqsHktNlf1wfJHHvJ8iifk32r} — a real, publicly committed 64-char literal. The same literal is the default across every prod compose file (prod-postgres.yml:85, prod-mysql.yml:85, prod-test.yml:52) plus the dev/test files. Backwards trace: config/settings/base.py:29 reads SECRET_KEY = env("DJANGO_SECRET_KEY") with NO in-code default, so the committed compose literal is the effective production SECRET_KEY whenever an operator fails to export SO

Although the secret is readable by an unauthenticated remote attacker (public repo) and at first looks like the 0-precondition/unauth HIGH row, exploitation is gated by at least two real preconditions: (1) the operator must fail to override SO_DJANGO_SECRET_KEY — the compose value is only a fallback default, and any prod deploy is expected to set it; and (2) the deployment must actually rely on a 
**Reachability evidence:** `backend/config/settings/base.py:29`, `docker-compose-prod-postgres.yml:85`

> Recommend a human build a PoC; static reasoning hit its limit.

### [MEDIUM] Committed default FIELD_ENCRYPTION_KEY in shipped prod compose defeats all at-rest field encryption  (f007)
`docker-compose-prod-postgres.yml:86` | hardcoded-secret | claimed HIGH (alignment -2) | confidence 0.9/10
**Owner:** component: deploy/compose; top committer Stefan Fleckenstein (28/50 recent commits); no CODEOWNERS
**Verdict:** mitigated, votes TP=3 FP=0 CV=0
**Preconditions (4):**
  - Operator did NOT set SO_FIELD_ENCRYPTION_KEY and accepted the committed default DtlkqVb3... — docs (configuration.md:24, installation.md) mark FIELD_ENCRYPTION_KEY as 'mandatory' with key-generation instructions, so a correctly configured deployment overrides it; the value is a ${VAR:-default} fallback, not a forced hardcoded secret.
  - Attacker obtains the at-rest ciphertext: a database dump, backup, DB credential, or other DB-level/backend access. The committed key alone is useless without the encrypted column values stored in the DB. There is NO path from the public HTTP/DRF surface to the DB contents.
  - For token forgery specifically: a JWT_Secret singleton row exists in the DB (created on first auth use) so JWT_Secret.secret ciphertext is present to decrypt; secret is signed/verified in jwt_authentication.py:31/69.
  - Attacker position is insider / DB-adjacent (stolen backup, separate DB-exposure bug, or operator/infra access) — not the modeled external HTTP/upload/OIDC attacker.
**Threat-model match:** Maps to "Compliance-scoped data exposure (integration secrets / crypto keys)" and the codebase's own THREAT_MODEL.md T3 ...
**Why:** Verified line 86 verbatim: FIELD_ENCRYPTION_KEY defaults to the committed public Fernet key DtlkqVb3wlaVdJK_BU-3mB4wwuuf8xx8YNInajiJ7GU= via ${SO_FIELD_ENCRYPTION_KEY:-...}. Backwards trace: base.py:432 reads env("FIELD_ENCRYPTION_KEY") with NO validation that it differs from the shipped default and NO fail-closed boot check (THREAT_MODEL.md:112 lists such a check as still-missing). The key drives django-encrypted-model-fields for every EncryptedCharField, including the security-critical ones: JWT_Secret.secret (access_control/models.py:104) and integration credentials api_key/basic_auth_passw

Verifier chain is technically correct: FIELD_ENCRYPTION_KEY (base.py:432) decrypts every EncryptedCharField including JWT_Secret.secret (access_control/models.py:104), and that secret signs/verifies all JWTs (jwt_authentication.py:31,69) plus Api_Configuration.api_key/basic_auth_password — so the default key + DB contents = forge any-user/superuser tokens and recover all integration secrets. But s
**Reachability evidence:** `backend/config/settings/base.py:432`, `docker-compose-prod-postgres.yml:86`

### [MEDIUM] NotificationViewSet.mark_as_viewed uses an unscoped lookup, allowing cross-product notification existence probing  (f015)
`backend/application/notifications/api/views.py:67` | idor | claimed LOW (alignment +2) | confidence 0.8/10
**Owner:** component: backend/notifications/api/; top committer Stefan Fleckenstein (2/3 recent commits); no CODEOWNERS
**Verdict:** exploitable, votes TP=3 FP=0 CV=0
**Preconditions (2):**
  - Attacker holds a valid authenticated session (any role, including lowest-priv Upload/Writer) — IsAuthenticated is still enforced at the class level; only the object-level product-scope check is bypassed.
  - Attacker supplies a notification pk to probe. PKs are sequential integers, so enumeration is trivial, but a target id must still be chosen — making this a 1-2 precondition, authenticated-access issue.
**Threat-model match:** Tenant-to-tenant data leakage (cross-product). The unscoped get_notification_by_id(pk) lets an authenticated user confir...
**Why:** Confirmed by reading the code. views.py:67-69: mark_as_viewed calls get_notification_by_id(pk), which (queries/notification.py:11-15) is unscoped Notification.objects.get(id=...). The product-scoped get_notifications() is wired only into get_queryset() (views.py:37-44), which DRF invokes via get_object() for standard retrieve/destroy. The custom detail action never calls get_object(), so UserHasNotificationPermission.has_object_permission (permissions.py:12) is never triggered. That permission class implements no has_permission method, so request-level checks pass; the only effective gate is I

Confirmed IDOR on mark_as_viewed; mechanically MEDIUM, impact is an existence-only oracle.
**Reachability evidence:** `backend/application/notifications/api/views.py:67`, `backend/config/api_router.py:105`

### [MEDIUM] Issue-tracker API key stored unencrypted at rest while sibling credentials use EncryptedCharField  (f002)
`backend/application/core/models.py:101` | sensitive-data-exposure | claimed HIGH (alignment -2) | confidence 0.8/10
**Owner:** component: backend/core/; top committer Stefan Fleckenstein (47/50 recent commits); no CODEOWNERS
**Verdict:** exploitable, votes TP=2 FP=1 CV=0
**Preconditions (3):**
  - A Maintainer/Owner has actually configured an issue tracker on a product, so issue_tracker_api_key is non-empty (field is blank=True and issue_tracker_active defaults False; with no tracker configured there is no secret to leak).
  - The credential is a live third-party token (GitHub PAT used as Bearer, GitLab PRIVATE-TOKEN, or Jira token) that is currently valid.
  - Attacker obtains a read channel to the secret: either (a) DB/backup/replica read access from a separate breach (the path in the verifier rationale), or (b) an authenticated session with read access to that product, since ProductSerializer uses fields='__all__' with no write_only/redaction and returns the plaintext field on read.
**Threat-model match:** Compliance-scoped data exposure (integration secrets / crypto keys): a live issue-tracker integration credential is stor...
**Why:** Verified directly. models.py:101 issue_tracker_api_key is a plain CharField (line 100 username likewise), confirmed by migration core/0012_issue_tracker.py:24-25 which creates a plaintext CharField column. The siblings the finding names are genuinely encrypted: access_control/models.py:104 JWT_Secret.secret, import_observations/models.py:44/49 Api_Configuration.api_key and basic_auth_password all use EncryptedCharField, and FIELD_ENCRYPTION_KEY is a required setting (config/settings/base.py:432), so encryption is operative — the gap is real, not a no-op. The token is functionally identical to 

Confirmed: issue_tracker_api_key (core/models.py:101) is a plain CharField holding a live tracker credential (Bearer at github_issue_tracker.py:124, PRIVATE-TOKEN at gitlab_issue_tracker.py:119, Jira token), while comparable secrets use EncryptedCharField (access_control/models.py:104; import_observations/models.py:44,49). Step 1 enumerates 2 preconditions: a tracker must be configured (field is o
**Reachability evidence:** `backend/application/core/api/serializers_product.py:101`, `backend/application/core/api/serializers_product.py:385 (ProductSerializer.validate accepts issue_tracker_api_key into attrs); persisted via core/models.py:101`, `backend/application/issue_tracker/issue_trackers/github_issue_tracker.py:124 (and gitlab_issue_tracker.py:119, jira_issue_tracker.py:22) read product.issue_tracker_api_key as a live auth token`

### [MEDIUM] OIDC username claim trusted as the local-account key, enabling account collision/takeover  (f018)
`backend/application/access_control/services/oidc_authentication.py:79` | auth-bypass | claimed HIGH (alignment -2) | confidence 0.7/10
**Owner:** component: backend/access_control/; top committer Stefan Fleckenstein (11/13 recent commits); no CODEOWNERS
**Verdict:** exploitable, votes TP=3 FP=0 CV=0
**Preconditions (4):**
  - OIDC authentication is enabled in the deployment (env OIDC_USERNAME / OIDC_AUTHORITY / OIDC_CLIENT_ID configured) — config-dependent, not all deployments use OIDC
  - OIDC_USERNAME is mapped to a mutable/self-asserted claim such as preferred_username rather than an immutable one (sub). If mapped to sub the attack does not work.
  - Attacker can obtain a validly-signed JWT from the configured IdP whose username claim equals a target user's username — i.e. they control an identity at the IdP and can set/edit that claim (self-registration, editable profile, or a federated second IdP), and the IdP does not enforce uniqueness/immutability of that claim against the target value
  - A target local or non-OIDC user with the colliding username already exists and is active (e.g. an 'admin' superuser created via createsuperuser); lookup is by username only with no is_oidc_user / issuer / sub binding
**Threat-model match:** Privilege escalation to admin (and tenant-to-tenant data leakage): impersonating an existing local 'admin'/superuser use...
**Why:** Confirmed at oidc_authentication.py:79-86. After full JWT validation (signature via IdP JWKS, audience=OIDC_CLIENT_ID, exp/iat/nbf), username=payload.get(os.environ["OIDC_USERNAME"]) is the SOLE key into get_user_by_username (queries/user.py:18-22, plain username lookup). There is NO iss/sub binding and NO is_oidc_user gate before the matched user is returned and authenticated. Crucially, _check_user_change (lines 160-165) retroactively flips is_oidc_user=True and unsets the existing user's password, silently converting a local account during the takeover. Call path: OIDCAuthentication is a DR

STEP 1 preconditions: (1) OIDC enabled, (2) OIDC_USERNAME mapped to a mutable claim like preferred_username not sub, (3) attacker controls an IdP identity and can set that claim to the victim's username on a JWT the configured IdP will sign, (4) a colliding local/non-OIDC username already exists and is active. The JWT is fully validated (verify_signature, strict_aud, exp/nbf/iat against the IdP JW
**Reachability evidence:** `backend/application/access_control/services/oidc_authentication.py:44`, `backend/application/access_control/services/oidc_authentication.py:44 (OIDCAuthentication.authenticate -> _validate_jwt, registered as a DRF authentication class; reachable on every authenticated API request bearing a Bearer token)`, `backend/config/settings/base.py:366 -> OIDCAuthentication registered as DEFAULT_AUTHENTICATION_CLASSES[0]; DRF invokes authenticate() at oidc_authentication.py:44 -> _validate_jwt() reaches line 79/82`

### [LOW] Teams/Slack webhook URL is user-controlled with no/weak host validation (blind SSRF)  (f020)
`backend/application/notifications/services/send_notifications_base.py:45` | ssrf | claimed LOW (alignment +2) | confidence 0.8/10
**Owner:** component: backend/notifications/; top committer Stefan Fleckenstein (1/1 recent commits); no CODEOWNERS
**Verdict:** exploitable, votes TP=2 FP=1 CV=0
**Preconditions (4):**
  - Attacker holds Maintainer/Owner role (Product_Edit permission) on a product, or is an admin/superuser to edit global Settings exception webhooks
  - Attacker sets notification_ms_teams_webhook / notification_slack_webhook (or global exception_*_webhook) to an internal/attacker-controlled URL; validate_url only enforces http/https scheme and explicitly permits localhost, and global Settings webhooks have no validator at all
  - A notification trigger fires: a security-gate status change on the product (e.g. via uploading a scanner report that flips the gate) or a backend exception for the global webhooks
  - Exploitation is blind only — requests POSTs body data to the URL but the response is discarded (only raise_for_status), so no data is returned to the attacker and no exfiltration of internal responses is possible
**Threat-model match:** No raising match. The closest stated threat is "Compliance-scoped data exposure (integration secrets / crypto keys)", bu...
**Why:** Confirmed at source. send_notifications_base.py:45 (msteams) and :68 (slack) issue requests.request(method="POST", url=webhook) where webhook is a stored, user-configured value. First call-site: send_notifications.py:52 passes _get_notification_ms_teams_webhook(product) straight in (slack at :62; exception variants at :98/:108 use global Settings).

Code confirms the finding: validate_url (serializers_helpers.py:48) checks only that scheme is http/https and explicitly allows localhost (simple_host), with no block on internal/link-local IPs (e.g. 169.254.169.254, 10.x, 192.168.x); global Settings exception webhooks have no validate_* method, so they are entirely unvalidated. send_msteams_notification / send_slack_notification (send_notificatio
**Reachability evidence:** `backend/application/notifications/services/send_notifications.py:52`

### [LOW] XLSX export (openpyxl) writes attacker-controllable fields into cells without formula-escaping  (f019)
`backend/application/commons/services/export.py:47` | csv-injection | claimed MEDIUM (alignment -1) | confidence 0.8/10
**Owner:** component: backend/commons/; top committer Stefan Fleckenstein (8/8 recent commits); no CODEOWNERS
**Verdict:** exploitable, votes TP=2 FP=1 CV=0
**Preconditions (6):**
  - Attacker has authenticated low-priv access (Upload/Writer) OR can submit an untrusted scanner report that gets imported
  - Attacker controls an observation field that reaches the export (e.g. title/description) and starts it with a formula trigger (= + - @)
  - The malicious data lands in a product the victim user is authorized to view (export queryset is permission-scoped)
  - A victim chooses the XLSX export specifically (the CSV path is neutralized via defusedcsv, so it must be the Excel export)
  - The victim opens the downloaded XLSX in a spreadsheet application
  - The victim dismisses/accepts the spreadsheet client's formula/external-data/macro warning so the formula actually evaluates
**Threat-model match:** No match. None of the four stated threats (tenant-to-tenant leakage, privilege escalation to admin, integration secret/c...
**Why:** Confirmed by reading export.py:47 directly: export_excel writes value straight into a cell via worksheet.cell(row, column, value=value) with NO formula-trigger neutralization, while the CSV sibling (export_csv, same file, line 63) explicitly uses defusedcsv. That asymmetry — one path defended, the parallel one not — refutes the "intended design" defense (rule 3): the project clearly intends to neutralize spreadsheet injection.

Confirmed real: export_excel writes attacker-influenced values straight into cells (export.py:47) with no formula-trigger neutralization, while the CSV sibling uses defusedcsv. Step 1 yields 6 concrete preconditions (authenticated/import access, formula-prefixed field, victim-accessible product, XLSX export specifically, victim opens file, victim accepts the client warning). Step 2: precondition c
**Reachability evidence:** `backend/application/core/api/views_observation.py:234`, `backend/application/core/services/export_observations.py:12`

### [LOW] Assessment approval gate bypassable by attaching a severity/VEX downgrade to an "In review" status change  (f009)
`backend/application/core/services/assessment.py:65` | broken-access-control | claimed MEDIUM (alignment -2) | confidence 0.8/10
**Owner:** component: backend/core/services/; top committer Stefan Fleckenstein (17/18 recent commits); no CODEOWNERS
**Verdict:** exploitable, votes TP=3 FP=0 CV=0
**Preconditions (4):**
  - Attacker is authenticated and holds a role granting Permissions.Observation_Assessment (Writer or higher) on the specific product/product-group containing the target observation (per-product, same-tenant scope).
  - The target product or its product group has assessments_need_approval=True; if approval is not required, all assessments are AUTO_APPROVED anyway and there is no control to bypass.
  - Attacker crafts the PATCH .../assessment request to bundle status='In review' together with the field change (severity/priority/vex) they want auto-applied, so the new_status != STATUS_IN_REVIEW clause short-circuits the NEEDS_APPROVAL branch to AUTO_APPROVED.
  - No prior assessment on that observation is currently in NEEDS_APPROVAL state (views_observation.py:142-146 rejects a new assessment while one awaits approval).
**Threat-model match:** None. The impact is a segregation-of-duties / approval-workflow bypass scoped to a product the user already has assessme...
**Why:** Confirmed in source. assessment.py:65-77 computes assessment_status = NEEDS_APPROVAL only if (assessments_need_approval) AND (some field changed) AND (new_status != STATUS_IN_REVIEW), else AUTO_APPROVED. The final AND term means that when new_status == "In review", the whole expression short-circuits to AUTO_APPROVED regardless of which other fields changed. Lines 79-91 then call _update_observation with the full submitted set (severity, status, priority, vex_justification, vex_remediations) applied independently of status. _update_observation (lines 132-158) applies each field on its own cond

Confirmed logic flaw: assessment.py:65-77 only sets NEEDS_APPROVAL when new_status != STATUS_IN_REVIEW, so bundling status='In review' with a severity/priority/vex change short-circuits to AUTO_APPROVED and _update_observation (line 83) applies the change with no second-party approver — defeating the assessments_need_approval control and the self-approval guard at line 233. Precondition count is 2
**Reachability evidence:** `backend/application/core/api/views_observation.py:148`

### [LOW] JSON structure breakout in Slack/Teams notifications via backslash in import-derived observation title  (f013)
`backend/application/notifications/services/send_notifications_base.py:43` | template-injection | claimed MEDIUM (alignment -2) | confidence 0.8/10
**Owner:** component: backend/notifications/; top committer Stefan Fleckenstein (1/1 recent commits); no CODEOWNERS
**Verdict:** exploitable, votes TP=3 FP=0 CV=0
**Preconditions (5):**
  - Attacker holds an in-tenant Upload or Writer role on a product, enabling import of an observation whose title (or feeds product.name) is attacker-controlled.
  - A Maintainer/Owner has previously configured an MS Teams or Slack webhook on the product or its product group (notification_ms_teams_webhook / notification_slack_webhook is non-empty).
  - The notification trigger gate is satisfied: the observation's severity/status/priority match the configured notification thresholds AND it is new or changed, so _create_notification_message actually fires and the payload is POSTed.
  - The crafted title must contain a backslash-quote sequence so that HTML autoescape (escapes " -> &quot; but not the backslash) followed by replace('&quot;', '\"') yields '\\"' = escaped-backslash + unescaped quote, breaking out of the JSON string.
  - For impact beyond a malformed/broken notification, the injected JSON must form structure meaningful to the downstream Teams/Slack endpoint (the org's own webhook, same tenant).
**Threat-model match:** None of the four stated threats. The injected JSON is POSTed only to the product's own tenant-scoped webhook (Teams/Slac...
**Why:** Confirmed at send_notifications_base.py:43 (Teams) and :65-66 (Slack): notification_message.replace("&quot;", '\"') on a hand-built JSON template string. Django's DjangoTemplates backend has autoescape ON by default and applies to ALL rendered files regardless of extension; only the email .tpl files opt out via {% autoescape off %}, while slack_observation.tpl / msteams_observation.tpl rely on default escaping — confirming autoescape is active on the vulnerable path. Django's escape() handles < > & " ' but leaves backslash untouched. observation.title is core/models.py:251 title = CharField(ma

The parity bug is real and confirmed: templates (msteams_observation.tpl, slack_observation.tpl) hand-build JSON with Django HTML autoescape, which escapes double-quotes to &quot; but leaves backslashes untouched; the downstream replace('&quot;', '\\\"') in send_notifications_base.py:43/66 then converts a title-embedded \\\" into \\\\\" = escaped-backslash + bare quote, terminating the JSON string
**Reachability evidence:** `backend/application/notifications/services/send_notifications_observation.py:109`, `backend/application/notifications/services/send_notifications_observation.py:119`

## Dropped

| id | title | file:line | why dropped |
|-----|-------|-----------|-------------|
| f025 | Unsanitized OpenVEX document_id_prefix reaches Content-Dispo... | `backend/application/vex/api/views.py:323` | duplicate of f021 |
| f003 | API-token auth loops Argon2 verify over every token in the D... | `backend/application/access_control/services/api_token_authentication.py:49` | intentional_behavior, not_actionable, excl rule 1 |
| f004 | Dependency-Track requests default to verify_ssl=False, sendi... | `backend/application/import_observations/models.py:51` | not_actionable, excl rule 13 |
| f005 | User-authored Rego policy can read the server process enviro... | `backend/application/rules/services/rego_interpreter.py:16` | implausible_trigger, intentional_behavior, excl rule 8 |
| f010 | NUL-byte stripping applied only to description; title and si... | `backend/application/core/services/observation.py:254` | not_actionable, excl rule 12 |
| f011 | Dependency-Track base_url is a user-set host with no allowli... | `backend/application/import_observations/parsers/dependency_track/parser.py:54` | intentional_behavior, excl rule 3 |
| f012 | GitLab PRIVATE-TOKEN sent to a user-controlled base_url with... | `backend/application/issue_tracker/issue_trackers/gitlab_issue_tracker.py:22` | intentional_behavior, excl rule 8 |
| f014 | JWT_Secret.load() empty-secret regeneration path is broken (... | `backend/application/access_control/models.py:119` | implausible_trigger, excl rule 13 |
| f016 | No account lockout on password auth; unauthenticated login/t... | `backend/application/access_control/api/views.py:318` | not_actionable, excl rule 13 |
| f017 | Committed default admin/admin credentials auto-create a supe... | `docker-compose-prod-postgres.yml:69` | intentional_behavior, excl rule 3 |
| f021 | Unsanitized user-controlled document_id_prefix injected into... | `backend/application/vex/api/views.py:447` | already_handled, not_actionable, excl rule 13 |
| f022 | Whole uploaded report parsed into memory with no content-siz... | `backend/application/import_observations/services/parser_detector.py:45` | intentional_behavior, not_actionable, excl rule 1 |
| f023 | Jira client uses a user-controlled server URL with basic_aut... | `backend/application/issue_tracker/issue_trackers/jira_issue_tracker.py:18` | intentional_behavior, excl rule 8 |
| f024 | No CPU/time/memory budget around Rego evaluation of untruste... | `backend/application/rules/services/rego_interpreter.py:23` | intentional_behavior, excl rule 1 |
| f026 | VEX document create/update views rely on default IsAuthentic... | `backend/application/vex/api/views.py:402` | not_actionable, excl rule 13 |
| f027 | Gitleaks secret redaction is a literal substring replace; mi... | `backend/application/import_observations/parsers/gitleaks/parser.py:67` | implausible_trigger, intentional_behavior, excl rule 13 |
| f028 | Email notification templates disable autoescaping on import-... | `backend/application/notifications/templates/email_observation.tpl:1` | intentional_behavior, misread_code, not_actionable, excl rule 12 |
| f029 | Unbounded recursion over attacker-nested CycloneDX component... | `backend/application/import_observations/parsers/cyclone_dx/parser.py:166` | already_handled, implausible_trigger, excl rule 1 |
| f030 | Attacker-controlled report text rendered as markdown in obse... | `backend/application/import_observations/parsers/sarif/parser.py:284` | already_handled, excl rule 14 |
