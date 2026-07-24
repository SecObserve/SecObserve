# secobserve

## Installing the chart

The chart can be installed from the OCI repository using `helm install secobserve --version 1.1.0 oci://ghcr.io/SecObserve/charts/secobserve`.

![Version: 1.1.0](https://img.shields.io/badge/Version-1.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.55.0](https://img.shields.io/badge/AppVersion-1.55.0-informational?style=flat-square)

A Helm chart to deploy SecObserve, an open-source vulnerability and license management system
designed for software development teams and cloud-native environments.

SecObserve helps teams identify, manage, and remediate security vulnerabilities and license compliance issues
across their software projects, enhancing visibility and improving DevSecOps workflows.

**Homepage:** <https://github.com/SecObserve/SecObserve>

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| SecObserve community |  |  |

## Source Code

* <https://github.com/SecObserve/SecObserve>

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| oci://registry-1.docker.io/bitnamicharts | postgresql | 16.x.x |

## Operational notes

The chart supports exactly one application replica because SecObserve currently uses a SQLite-backed Huey task queue. The queue is persisted in a dedicated PersistentVolumeClaim by default.

Application and bundled PostgreSQL resource names are derived from the Helm release name. External databases can be configured through `database.*` values with `postgresql.enabled=false`.

## Values

### Pod

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | Sets the affinity for the secobserve pod For more information on affinity, see https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity |
| extraInitContainers | list | `[]` | additional init containers to add to the SecObserve Pod |
| labels | object | `{}` | additional labels to add to the SecObserve Pod |
| nodeSelector | object | `{}` | Node labels to select for secobserve pod assignment |
| podAnnotations | object | `{}` | annotations to add to the SecObserve Pod |
| replicaCount | int | `1` | number of replicas to deploy |
| securityContext | object | `{"enabled":true,"fsGroup":1001,"fsGroupChangePolicy":"OnRootMismatch"}` | securityContext to use for the pod |
| tolerations | object | `{}` | Toleration labels for pod assignment |

### Backend

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| backend.env[0] | object | `{"name":"ADMIN_USER","value":"admin"}` | admin user name |
| backend.env[10] | object | `{"name":"OIDC_EMAIL","value":"email"}` | OIDC email address |
| backend.env[11] | object | `{"name":"OIDC_GROUPS","value":"groups"}` | OIDC groups |
| backend.env[1] | object | `{"name":"ADMIN_EMAIL","value":"admin@admin.com"}` | admin email address |
| backend.env[2] | object | `{"name":"ALLOWED_HOSTS","value":"secobserve.dev"}` | allowed hosts |
| backend.env[3] | object | `{"name":"CORS_ALLOWED_ORIGINS","value":"https://secobserve.dev"}` | CORS allowed origins |
| backend.env[4] | object | `{"name":"OIDC_AUTHORITY","value":"https://oidc.secobserve.dev"}` | admin OIDC authority |
| backend.env[5] | object | `{"name":"OIDC_CLIENT_ID","value":"secobserve"}` | OIDC client id |
| backend.env[6] | object | `{"name":"OIDC_USERNAME","value":"preferred_username"}` | OIDC user name |
| backend.env[7] | object | `{"name":"OIDC_FIRST_NAME","value":"given_name"}` | OIDC first name |
| backend.env[8] | object | `{"name":"OIDC_LAST_NAME","value":"family_name"}` | OIDC last name |
| backend.env[9] | object | `{"name":"OIDC_FULL_NAME","value":"preferred_username"}` | OIDC full name |
| backend.existingSecret | string | `""` | existing Secret containing the admin password, Django secret key and field encryption key |
| backend.image | object | `{"pullPolicy":"IfNotPresent","registry":"ghcr.io","repository":"secobserve/secobserve-backend","tag":null}` | image registry |
| backend.image.pullPolicy | string | `"IfNotPresent"` | image pull policy |
| backend.image.repository | string | `"secobserve/secobserve-backend"` | image repository |
| backend.image.tag | string | `nil` | image tag (uses appVersion value of Chart.yaml if not specified) |
| backend.resources | object | `{"limits":{"cpu":"1000m","memory":"1500Mi"},"requests":{"cpu":"1000m","memory":"1500Mi"}}` | resource requirements and limits |
| backend.secretKeys.adminPassword | string | `"password"` | key containing the initial admin password |
| backend.secretKeys.djangoSecretKey | string | `"django_secret_key"` | key containing the Django secret key |
| backend.secretKeys.fieldEncryptionKey | string | `"field_encryption_key"` | key containing the field encryption key |
| backend.securityContext | object | `{"allowPrivilegeEscalation":false,"enabled":true,"runAsGroup":1001,"runAsNonRoot":true,"runAsUser":1001}` | security context to use for the backend container |
| backend.service.port | int | `5000` | service port |
| backend.volumeMounts | list | `[]` | additional volume mounts for the backend container |
| backend.volumes | list | `[]` | additional Pod volumes used by the backend container |

### Database

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| database.engine | string | `"django.db.backends.postgresql"` | Django database engine |
| database.host | string | `""` | database hostname; inferred from the bundled PostgreSQL chart when empty |
| database.name | string | `""` | database name; defaults to postgresql.auth.database when empty |
| database.passwordSecret.key | string | `""` | key containing the database password; inferred from PostgreSQL values when empty |
| database.passwordSecret.name | string | `""` | Secret containing the database password; inferred from PostgreSQL values when empty |
| database.port | int | `5432` | database port |
| database.username | string | `""` | database username; defaults to postgresql.auth.username when empty |

### dbchecker

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| dbchecker.enabled | bool | `true` | enable the database readiness init container |
| dbchecker.hostname | string | `""` | database hostname override; inferred from database settings when empty |
| dbchecker.image.digest | string | `""` | Image digest for the dbchecker image; takes precedence over tag when set |
| dbchecker.image.pullPolicy | string | `"IfNotPresent"` | Image pull policy for the dbchecker image |
| dbchecker.image.repository | string | `"busybox"` | Docker image used to check Database readiness at startup |
| dbchecker.image.tag | string | `"1.37.0"` | Image tag for the dbchecker image |
| dbchecker.port | int | `5432` | database port checked by the init container |
| dbchecker.resources | object | `{"limits":{"cpu":"20m","memory":"32Mi"},"requests":{"cpu":"20m","memory":"32Mi"}}` | Resource requests and limits for the dbchecker container |
| dbchecker.securityContext | object | `{"allowPrivilegeEscalation":false,"enabled":true,"runAsGroup":1001,"runAsNonRoot":true,"runAsUser":1001}` | SecurityContext for the dbchecker container |

### Frontend

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.env[0] | object | `{"name":"API_BASE_URL","value":"https://secobserve.dev/api"}` | Base URL for API |
| frontend.env[1] | object | `{"name":"OIDC_ENABLE","value":"false"}` | enable OIDC authentication |
| frontend.env[2] | object | `{"name":"OIDC_AUTHORITY","value":"https://oidc.secobserve.dev"}` | oidc issuer |
| frontend.env[3] | object | `{"name":"OIDC_CLIENT_ID","value":"secobserve"}` | OIDC client ID |
| frontend.env[4] | object | `{"name":"OIDC_REDIRECT_URI","value":"https://secobserve.dev/"}` | OIDC client redirect URL |
| frontend.env[5] | object | `{"name":"OIDC_POST_LOGOUT_REDIRECT_URI","value":"https://secobserve.dev/"}` | URI to redirect to after logout |
| frontend.env[6] | object | `{"name":"OIDC_PROMPT","value":null}` | OIDC prompt |
| frontend.image.pullPolicy | string | `"IfNotPresent"` | image pull policy |
| frontend.image.registry | string | `"ghcr.io"` | image registry |
| frontend.image.repository | string | `"secobserve/secobserve-frontend"` | image repository |
| frontend.image.tag | string | `nil` | image tag (uses appVersion value of Chart.yaml if not specified) |
| frontend.resources | object | `{"limits":{"cpu":"500m","memory":"1000Mi"},"requests":{"cpu":"500m","memory":"1000Mi"}}` | resource requirements and limits |
| frontend.securityContext | object | `{"allowPrivilegeEscalation":false,"enabled":true,"runAsGroup":1001,"runAsNonRoot":true,"runAsUser":1001}` | securityContext to use for frontend container |
| frontend.service.port | int | `3000` | service port |
| frontend.volumeMounts | list | `[]` | additional volume mounts for the frontend container |
| frontend.volumes | list | `[]` | additional Pod volumes used by the frontend container |

### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| fullnameOverride | string | `""` | fully override generated resource names |
| nameOverride | string | `""` | override the chart name used in resource names |

### Huey

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| huey.persistence.accessModes | list | `["ReadWriteOnce"]` | access modes for the Huey PersistentVolumeClaim |
| huey.persistence.annotations | object | `{}` | annotations to add to the Huey PersistentVolumeClaim |
| huey.persistence.enabled | bool | `true` | persist the Huey SQLite queue across backend container and Pod restarts |
| huey.persistence.existingClaim | string | `""` | use an existing PersistentVolumeClaim instead of creating one |
| huey.persistence.size | string | `"1Gi"` | requested storage size for the Huey PersistentVolumeClaim |
| huey.persistence.storageClass | string | `""` | storage class for the Huey PersistentVolumeClaim; use "-" to disable dynamic provisioning |

### Ingress

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| ingress.annotations | object | `{"kubernetes.io/ingress.class":"nginx","nginx.ingress.kubernetes.io/proxy-read-timeout":"600","nginx.ingress.kubernetes.io/proxy-send-timeout":"600","nginx.ingress.kubernetes.io/ssl-redirect":"true"}` | annotations to add to ingress |
| ingress.enabled | bool | `true` | If true, a Kubernetes Ingress resource will be created to the http port of the secobserve Service |
| ingress.hostname | string | `"secobserve.dev"` | hostname of ingress |
| ingress.ingressClassName | string | `"nginx"` | ingress class name |
| ingress.paths | list | `[]` | additional paths appended to the generated ingress rule |

### Postgresql

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| postgresql.architecture | string | `"standalone"` | PostgreSQL architecture (`standalone` or `replication`) |
| postgresql.auth | object | `{"database":"secobserve","existingSecret":"","password":"","postgresPassword":"","secretKeys":{"userPasswordKey":"password"},"username":"secobserve"}` | authentication settings for the bundled PostgreSQL database |
| postgresql.auth.database | string | `"secobserve"` | Name for a custom database to create |
| postgresql.auth.existingSecret | string | `""` | Name of existing secret to use for PostgreSQL credentials |
| postgresql.auth.password | string | `""` | Password for the custom user to create |
| postgresql.auth.postgresPassword | string | `""` | Password for the "postgres" admin user. Ignored if `auth.existingSecret` with key `postgres-password` is provided |
| postgresql.auth.secretKeys.userPasswordKey | string | `"password"` | Name of key in existing secret to use for PostgreSQL credentials. Only used when `auth.existingSecret` is set. |
| postgresql.auth.username | string | `"secobserve"` | Name for a custom user to create |
| postgresql.enabled | bool | `true` | Switch to enable or disable the PostgreSQL helm chart |
| postgresql.image | object | `{"repository":"bitnamilegacy/postgresql"}` | image repository override for the bundled PostgreSQL database |
| postgresql.metrics | object | `{"image":{"repository":"bitnamilegacy/postgres-exporter"}}` | image repository overrides for PostgreSQL metrics |
| postgresql.volumePermissions | object | `{"image":{"repository":"bitnamilegacy/os-shell"}}` | image repository overrides for the volume-permissions init container |

### Service

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| service | object | `{"annotations":{},"type":"ClusterIP"}` | defines the secobserve http service |
| service.annotations | object | `{}` | annotations to add to the Service |
| service.type | string | `"ClusterIP"` | Service type of service |

## Values

<h3>Pod</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>affinity</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>Sets the affinity for the secobserve pod For more information on affinity, see https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity</td>
		</tr>
		<tr>
			<td>extraInitContainers</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>additional init containers to add to the SecObserve Pod</td>
		</tr>
		<tr>
			<td>labels</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>additional labels to add to the SecObserve Pod</td>
		</tr>
		<tr>
			<td>nodeSelector</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>Node labels to select for secobserve pod assignment</td>
		</tr>
		<tr>
			<td>podAnnotations</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>annotations to add to the SecObserve Pod</td>
		</tr>
		<tr>
			<td>replicaCount</td>
			<td>int</td>
			<td><pre lang="json">
1
</pre>
</td>
			<td>number of replicas to deploy</td>
		</tr>
		<tr>
			<td>securityContext</td>
			<td>object</td>
			<td><pre lang="json">
{
  "enabled": true,
  "fsGroup": 1001,
  "fsGroupChangePolicy": "OnRootMismatch"
}
</pre>
</td>
			<td>securityContext to use for the pod</td>
		</tr>
		<tr>
			<td>tolerations</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>Toleration labels for pod assignment</td>
		</tr>
	</tbody>
</table>
<h3>Backend</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>backend.env[0]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "ADMIN_USER",
  "value": "admin"
}
</pre>
</td>
			<td>admin user name</td>
		</tr>
		<tr>
			<td>backend.env[10]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_EMAIL",
  "value": "email"
}
</pre>
</td>
			<td>OIDC email address</td>
		</tr>
		<tr>
			<td>backend.env[11]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_GROUPS",
  "value": "groups"
}
</pre>
</td>
			<td>OIDC groups</td>
		</tr>
		<tr>
			<td>backend.env[1]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "ADMIN_EMAIL",
  "value": "admin@admin.com"
}
</pre>
</td>
			<td>admin email address</td>
		</tr>
		<tr>
			<td>backend.env[2]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "ALLOWED_HOSTS",
  "value": "secobserve.dev"
}
</pre>
</td>
			<td>allowed hosts</td>
		</tr>
		<tr>
			<td>backend.env[3]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "CORS_ALLOWED_ORIGINS",
  "value": "https://secobserve.dev"
}
</pre>
</td>
			<td>CORS allowed origins</td>
		</tr>
		<tr>
			<td>backend.env[4]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_AUTHORITY",
  "value": "https://oidc.secobserve.dev"
}
</pre>
</td>
			<td>admin OIDC authority</td>
		</tr>
		<tr>
			<td>backend.env[5]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_CLIENT_ID",
  "value": "secobserve"
}
</pre>
</td>
			<td>OIDC client id</td>
		</tr>
		<tr>
			<td>backend.env[6]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_USERNAME",
  "value": "preferred_username"
}
</pre>
</td>
			<td>OIDC user name</td>
		</tr>
		<tr>
			<td>backend.env[7]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_FIRST_NAME",
  "value": "given_name"
}
</pre>
</td>
			<td>OIDC first name</td>
		</tr>
		<tr>
			<td>backend.env[8]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_LAST_NAME",
  "value": "family_name"
}
</pre>
</td>
			<td>OIDC last name</td>
		</tr>
		<tr>
			<td>backend.env[9]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_FULL_NAME",
  "value": "preferred_username"
}
</pre>
</td>
			<td>OIDC full name</td>
		</tr>
		<tr>
			<td>backend.existingSecret</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>existing Secret containing the admin password, Django secret key and field encryption key</td>
		</tr>
		<tr>
			<td>backend.image</td>
			<td>object</td>
			<td><pre lang="json">
{
  "pullPolicy": "IfNotPresent",
  "registry": "ghcr.io",
  "repository": "secobserve/secobserve-backend",
  "tag": null
}
</pre>
</td>
			<td>image registry</td>
		</tr>
		<tr>
			<td>backend.image.pullPolicy</td>
			<td>string</td>
			<td><pre lang="json">
"IfNotPresent"
</pre>
</td>
			<td>image pull policy</td>
		</tr>
		<tr>
			<td>backend.image.repository</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve/secobserve-backend"
</pre>
</td>
			<td>image repository</td>
		</tr>
		<tr>
			<td>backend.image.tag</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td>image tag (uses appVersion value of Chart.yaml if not specified)</td>
		</tr>
		<tr>
			<td>backend.resources</td>
			<td>object</td>
			<td><pre lang="json">
{
  "limits": {
    "cpu": "1000m",
    "memory": "1500Mi"
  },
  "requests": {
    "cpu": "1000m",
    "memory": "1500Mi"
  }
}
</pre>
</td>
			<td>resource requirements and limits</td>
		</tr>
		<tr>
			<td>backend.secretKeys.adminPassword</td>
			<td>string</td>
			<td><pre lang="json">
"password"
</pre>
</td>
			<td>key containing the initial admin password</td>
		</tr>
		<tr>
			<td>backend.secretKeys.djangoSecretKey</td>
			<td>string</td>
			<td><pre lang="json">
"django_secret_key"
</pre>
</td>
			<td>key containing the Django secret key</td>
		</tr>
		<tr>
			<td>backend.secretKeys.fieldEncryptionKey</td>
			<td>string</td>
			<td><pre lang="json">
"field_encryption_key"
</pre>
</td>
			<td>key containing the field encryption key</td>
		</tr>
		<tr>
			<td>backend.securityContext</td>
			<td>object</td>
			<td><pre lang="json">
{
  "allowPrivilegeEscalation": false,
  "enabled": true,
  "runAsGroup": 1001,
  "runAsNonRoot": true,
  "runAsUser": 1001
}
</pre>
</td>
			<td>security context to use for the backend container</td>
		</tr>
		<tr>
			<td>backend.service.port</td>
			<td>int</td>
			<td><pre lang="json">
5000
</pre>
</td>
			<td>service port</td>
		</tr>
		<tr>
			<td>backend.volumeMounts</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>additional volume mounts for the backend container</td>
		</tr>
		<tr>
			<td>backend.volumes</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>additional Pod volumes used by the backend container</td>
		</tr>
	</tbody>
</table>
<h3>Database</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>database.engine</td>
			<td>string</td>
			<td><pre lang="json">
"django.db.backends.postgresql"
</pre>
</td>
			<td>Django database engine</td>
		</tr>
		<tr>
			<td>database.host</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>database hostname; inferred from the bundled PostgreSQL chart when empty</td>
		</tr>
		<tr>
			<td>database.name</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>database name; defaults to postgresql.auth.database when empty</td>
		</tr>
		<tr>
			<td>database.passwordSecret.key</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>key containing the database password; inferred from PostgreSQL values when empty</td>
		</tr>
		<tr>
			<td>database.passwordSecret.name</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>Secret containing the database password; inferred from PostgreSQL values when empty</td>
		</tr>
		<tr>
			<td>database.port</td>
			<td>int</td>
			<td><pre lang="json">
5432
</pre>
</td>
			<td>database port</td>
		</tr>
		<tr>
			<td>database.username</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>database username; defaults to postgresql.auth.username when empty</td>
		</tr>
	</tbody>
</table>
<h3>dbchecker</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>dbchecker.enabled</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td>enable the database readiness init container</td>
		</tr>
		<tr>
			<td>dbchecker.hostname</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>database hostname override; inferred from database settings when empty</td>
		</tr>
		<tr>
			<td>dbchecker.image.digest</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>Image digest for the dbchecker image; takes precedence over tag when set</td>
		</tr>
		<tr>
			<td>dbchecker.image.pullPolicy</td>
			<td>string</td>
			<td><pre lang="json">
"IfNotPresent"
</pre>
</td>
			<td>Image pull policy for the dbchecker image</td>
		</tr>
		<tr>
			<td>dbchecker.image.repository</td>
			<td>string</td>
			<td><pre lang="json">
"busybox"
</pre>
</td>
			<td>Docker image used to check Database readiness at startup</td>
		</tr>
		<tr>
			<td>dbchecker.image.tag</td>
			<td>string</td>
			<td><pre lang="json">
"1.37.0"
</pre>
</td>
			<td>Image tag for the dbchecker image</td>
		</tr>
		<tr>
			<td>dbchecker.port</td>
			<td>int</td>
			<td><pre lang="json">
5432
</pre>
</td>
			<td>database port checked by the init container</td>
		</tr>
		<tr>
			<td>dbchecker.resources</td>
			<td>object</td>
			<td><pre lang="json">
{
  "limits": {
    "cpu": "20m",
    "memory": "32Mi"
  },
  "requests": {
    "cpu": "20m",
    "memory": "32Mi"
  }
}
</pre>
</td>
			<td>Resource requests and limits for the dbchecker container</td>
		</tr>
		<tr>
			<td>dbchecker.securityContext</td>
			<td>object</td>
			<td><pre lang="json">
{
  "allowPrivilegeEscalation": false,
  "enabled": true,
  "runAsGroup": 1001,
  "runAsNonRoot": true,
  "runAsUser": 1001
}
</pre>
</td>
			<td>SecurityContext for the dbchecker container</td>
		</tr>
	</tbody>
</table>
<h3>Frontend</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>frontend.env[0]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "API_BASE_URL",
  "value": "https://secobserve.dev/api"
}
</pre>
</td>
			<td>Base URL for API</td>
		</tr>
		<tr>
			<td>frontend.env[1]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_ENABLE",
  "value": "false"
}
</pre>
</td>
			<td>enable OIDC authentication</td>
		</tr>
		<tr>
			<td>frontend.env[2]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_AUTHORITY",
  "value": "https://oidc.secobserve.dev"
}
</pre>
</td>
			<td>oidc issuer</td>
		</tr>
		<tr>
			<td>frontend.env[3]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_CLIENT_ID",
  "value": "secobserve"
}
</pre>
</td>
			<td>OIDC client ID</td>
		</tr>
		<tr>
			<td>frontend.env[4]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_REDIRECT_URI",
  "value": "https://secobserve.dev/"
}
</pre>
</td>
			<td>OIDC client redirect URL</td>
		</tr>
		<tr>
			<td>frontend.env[5]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_POST_LOGOUT_REDIRECT_URI",
  "value": "https://secobserve.dev/"
}
</pre>
</td>
			<td>URI to redirect to after logout</td>
		</tr>
		<tr>
			<td>frontend.env[6]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "OIDC_PROMPT",
  "value": null
}
</pre>
</td>
			<td>OIDC prompt</td>
		</tr>
		<tr>
			<td>frontend.image.pullPolicy</td>
			<td>string</td>
			<td><pre lang="json">
"IfNotPresent"
</pre>
</td>
			<td>image pull policy</td>
		</tr>
		<tr>
			<td>frontend.image.registry</td>
			<td>string</td>
			<td><pre lang="json">
"ghcr.io"
</pre>
</td>
			<td>image registry</td>
		</tr>
		<tr>
			<td>frontend.image.repository</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve/secobserve-frontend"
</pre>
</td>
			<td>image repository</td>
		</tr>
		<tr>
			<td>frontend.image.tag</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td>image tag (uses appVersion value of Chart.yaml if not specified)</td>
		</tr>
		<tr>
			<td>frontend.resources</td>
			<td>object</td>
			<td><pre lang="json">
{
  "limits": {
    "cpu": "500m",
    "memory": "1000Mi"
  },
  "requests": {
    "cpu": "500m",
    "memory": "1000Mi"
  }
}
</pre>
</td>
			<td>resource requirements and limits</td>
		</tr>
		<tr>
			<td>frontend.securityContext</td>
			<td>object</td>
			<td><pre lang="json">
{
  "allowPrivilegeEscalation": false,
  "enabled": true,
  "runAsGroup": 1001,
  "runAsNonRoot": true,
  "runAsUser": 1001
}
</pre>
</td>
			<td>securityContext to use for frontend container</td>
		</tr>
		<tr>
			<td>frontend.service.port</td>
			<td>int</td>
			<td><pre lang="json">
3000
</pre>
</td>
			<td>service port</td>
		</tr>
		<tr>
			<td>frontend.volumeMounts</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>additional volume mounts for the frontend container</td>
		</tr>
		<tr>
			<td>frontend.volumes</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>additional Pod volumes used by the frontend container</td>
		</tr>
	</tbody>
</table>
<h3>General</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>fullnameOverride</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>fully override generated resource names</td>
		</tr>
		<tr>
			<td>nameOverride</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>override the chart name used in resource names</td>
		</tr>
	</tbody>
</table>
<h3>Huey</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>huey.persistence.accessModes</td>
			<td>list</td>
			<td><pre lang="json">
[
  "ReadWriteOnce"
]
</pre>
</td>
			<td>access modes for the Huey PersistentVolumeClaim</td>
		</tr>
		<tr>
			<td>huey.persistence.annotations</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>annotations to add to the Huey PersistentVolumeClaim</td>
		</tr>
		<tr>
			<td>huey.persistence.enabled</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td>persist the Huey SQLite queue across backend container and Pod restarts</td>
		</tr>
		<tr>
			<td>huey.persistence.existingClaim</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>use an existing PersistentVolumeClaim instead of creating one</td>
		</tr>
		<tr>
			<td>huey.persistence.size</td>
			<td>string</td>
			<td><pre lang="json">
"1Gi"
</pre>
</td>
			<td>requested storage size for the Huey PersistentVolumeClaim</td>
		</tr>
		<tr>
			<td>huey.persistence.storageClass</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>storage class for the Huey PersistentVolumeClaim; use "-" to disable dynamic provisioning</td>
		</tr>
	</tbody>
</table>
<h3>Ingress</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>ingress.annotations</td>
			<td>object</td>
			<td><pre lang="json">
{
  "kubernetes.io/ingress.class": "nginx",
  "nginx.ingress.kubernetes.io/proxy-read-timeout": "600",
  "nginx.ingress.kubernetes.io/proxy-send-timeout": "600",
  "nginx.ingress.kubernetes.io/ssl-redirect": "true"
}
</pre>
</td>
			<td>annotations to add to ingress</td>
		</tr>
		<tr>
			<td>ingress.enabled</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td>If true, a Kubernetes Ingress resource will be created to the http port of the secobserve Service</td>
		</tr>
		<tr>
			<td>ingress.hostname</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve.dev"
</pre>
</td>
			<td>hostname of ingress</td>
		</tr>
		<tr>
			<td>ingress.ingressClassName</td>
			<td>string</td>
			<td><pre lang="json">
"nginx"
</pre>
</td>
			<td>ingress class name</td>
		</tr>
		<tr>
			<td>ingress.paths</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>additional paths appended to the generated ingress rule</td>
		</tr>
	</tbody>
</table>
<h3>Postgresql</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>postgresql.architecture</td>
			<td>string</td>
			<td><pre lang="json">
"standalone"
</pre>
</td>
			<td>PostgreSQL architecture (`standalone` or `replication`)</td>
		</tr>
		<tr>
			<td>postgresql.auth</td>
			<td>object</td>
			<td><pre lang="json">
{
  "database": "secobserve",
  "existingSecret": "",
  "password": "",
  "postgresPassword": "",
  "secretKeys": {
    "userPasswordKey": "password"
  },
  "username": "secobserve"
}
</pre>
</td>
			<td>authentication settings for the bundled PostgreSQL database</td>
		</tr>
		<tr>
			<td>postgresql.auth.database</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve"
</pre>
</td>
			<td>Name for a custom database to create</td>
		</tr>
		<tr>
			<td>postgresql.auth.existingSecret</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>Name of existing secret to use for PostgreSQL credentials</td>
		</tr>
		<tr>
			<td>postgresql.auth.password</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>Password for the custom user to create</td>
		</tr>
		<tr>
			<td>postgresql.auth.postgresPassword</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td>Password for the "postgres" admin user. Ignored if `auth.existingSecret` with key `postgres-password` is provided</td>
		</tr>
		<tr>
			<td>postgresql.auth.secretKeys.userPasswordKey</td>
			<td>string</td>
			<td><pre lang="json">
"password"
</pre>
</td>
			<td>Name of key in existing secret to use for PostgreSQL credentials. Only used when `auth.existingSecret` is set.</td>
		</tr>
		<tr>
			<td>postgresql.auth.username</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve"
</pre>
</td>
			<td>Name for a custom user to create</td>
		</tr>
		<tr>
			<td>postgresql.enabled</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td>Switch to enable or disable the PostgreSQL helm chart</td>
		</tr>
		<tr>
			<td>postgresql.image</td>
			<td>object</td>
			<td><pre lang="json">
{
  "repository": "bitnamilegacy/postgresql"
}
</pre>
</td>
			<td>image repository override for the bundled PostgreSQL database</td>
		</tr>
		<tr>
			<td>postgresql.metrics</td>
			<td>object</td>
			<td><pre lang="json">
{
  "image": {
    "repository": "bitnamilegacy/postgres-exporter"
  }
}
</pre>
</td>
			<td>image repository overrides for PostgreSQL metrics</td>
		</tr>
		<tr>
			<td>postgresql.volumePermissions</td>
			<td>object</td>
			<td><pre lang="json">
{
  "image": {
    "repository": "bitnamilegacy/os-shell"
  }
}
</pre>
</td>
			<td>image repository overrides for the volume-permissions init container</td>
		</tr>
	</tbody>
</table>
<h3>Service</h3>
<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>service</td>
			<td>object</td>
			<td><pre lang="json">
{
  "annotations": {},
  "type": "ClusterIP"
}
</pre>
</td>
			<td>defines the secobserve http service</td>
		</tr>
		<tr>
			<td>service.annotations</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>annotations to add to the Service</td>
		</tr>
		<tr>
			<td>service.type</td>
			<td>string</td>
			<td><pre lang="json">
"ClusterIP"
</pre>
</td>
			<td>Service type of service</td>
		</tr>
	</tbody>
</table>

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
