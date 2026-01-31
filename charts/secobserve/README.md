# secobserve

## Installing the chart

The chart can be installed as from the OCI repository using `helm install secobserve --version 1.47.2 oci://ghcr.io/SecObserve/charts/secobserve`.

![Version: 1.0.16](https://img.shields.io/badge/Version-1.0.16-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.47.2](https://img.shields.io/badge/AppVersion-1.47.2-informational?style=flat-square)

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

## Values

### Pod

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | Sets the affinity for the secobserve pod For more information on affinity, see https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity |
| nodeSelector | object | `{}` | Node labels to select for secobserve pod assignment |
| replicaCount | int | `1` | number of replicas to deploy |
| tolerations | object | `{}` | Toleration labels for pod assignment |

### Backend

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| backend.env[0] | object | `{"name":"ADMIN_USER","value":"admin"}` | admin user name |
| backend.env[10] | object | `{"name":"CORS_ALLOWED_ORIGINS","value":"https://secobserve.dev"}` | CORS allowed origins |
| backend.env[11] | object | `{"name":"DJANGO_SECRET_KEY","valueFrom":{"secretKeyRef":{"key":"django_secret_key","name":"secobserve-secrets"}}}` | django secret key |
| backend.env[11].valueFrom.secretKeyRef | object | `{"key":"django_secret_key","name":"secobserve-secrets"}` | secret name containing the django secret key |
| backend.env[12] | object | `{"name":"FIELD_ENCRYPTION_KEY","valueFrom":{"secretKeyRef":{"key":"field_encryption_key","name":"secobserve-secrets"}}}` | encryption key for fields |
| backend.env[12].valueFrom.secretKeyRef | object | `{"key":"field_encryption_key","name":"secobserve-secrets"}` | secret name containig the field encryption key |
| backend.env[13] | object | `{"name":"OIDC_AUTHORITY","value":"https://oidc.secobserve.dev"}` | admin OIDC authority |
| backend.env[14] | object | `{"name":"OIDC_CLIENT_ID","value":"secobserve"}` | OIDC client id |
| backend.env[15] | object | `{"name":"OIDC_USERNAME","value":"preferred_username"}` | OIDC user name |
| backend.env[16] | object | `{"name":"OIDC_FIRST_NAME","value":"given_name"}` | OIDC first name |
| backend.env[17] | object | `{"name":"OIDC_LAST_NAME","value":"family_name"}` | OIDC last name |
| backend.env[18] | object | `{"name":"OIDC_FULL_NAME","value":"preferred_username"}` | OIDC full name |
| backend.env[19] | object | `{"name":"OIDC_EMAIL","value":"email"}` | OIDC email address |
| backend.env[1] | object | `{"name":"ADMIN_PASSWORD","valueFrom":{"secretKeyRef":{"key":"password","name":"secobserve-secrets"}}}` | admin password |
| backend.env[20] | object | `{"name":"OIDC_GROUPS","value":"groups"}` | OIDC groups |
| backend.env[2] | object | `{"name":"ADMIN_EMAIL","value":"admin@admin.com"}` | admin email address |
| backend.env[3] | object | `{"name":"DATABASE_ENGINE","value":"django.db.backends.postgresql"}` | database engine |
| backend.env[4] | object | `{"name":"DATABASE_HOST","value":"secobserve-postgresql"}` | database host/service |
| backend.env[5] | object | `{"name":"DATABASE_PORT","value":"5432"}` | database port |
| backend.env[6] | object | `{"name":"DATABASE_DB","value":"secobserve"}` | database name |
| backend.env[7] | object | `{"name":"DATABASE_USER","value":"secobserve"}` | database user |
| backend.env[8] | object | `{"name":"DATABASE_PASSWORD","valueFrom":{"secretKeyRef":{"key":"password","name":"secobserve-postgresql"}}}` | database password |
| backend.env[8].valueFrom.secretKeyRef | object | `{"key":"password","name":"secobserve-postgresql"}` | reference to secret containing db credentials |
| backend.env[9] | object | `{"name":"ALLOWED_HOSTS","value":"secobserve.dev"}` | allowed hosts |
| backend.image | object | `{"pullPolicy":"IfNotPresent","registry":"ghcr.io","repository":"secobserve/secobserve-backend","tag":null}` | image registry |
| backend.image.pullPolicy | string | `"IfNotPresent"` | image pull policy |
| backend.image.repository | string | `"secobserve/secobserve-backend"` | image repository |
| backend.image.tag | string | `nil` | image tag (uses appVersion value of Chart.yaml if not specified) |
| backend.resources | object | `{"limits":{"cpu":"1000m","memory":"1500Mi"},"requests":{"cpu":"1000m","memory":"1500Mi"}}` | resource requirements and limits |
| backend.securityContext | object | `{"allowPrivilegeEscalation":false,"enabled":true,"runAsGroup":1001,"runAsNonRoot":true,"runAsUser":1001}` | security context to use for backend pod |
| backend.service.port | int | `5000` | service port |

### dbchecker

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| dbchecker.enabled | bool | `true` | enable dbchecker init container |
| dbchecker.hostname | string | `"secobserve-postgresql"` | enable dbchecker init container |
| dbchecker.image.pullPolicy | string | `"IfNotPresent"` | Image pull policy for the dbchecker image |
| dbchecker.image.repository | string | `"busybox"` | Docker image used to check Database readiness at startup |
| dbchecker.image.tag | string | `"latest"` | Image tag for the dbchecker image |
| dbchecker.port | int | `5432` | enable dbchecker init container |
| dbchecker.resources | object | `{"limits":{"cpu":"20m","memory":"32Mi"},"requests":{"cpu":"20m","memory":"32Mi"}}` | Resource requests and limits for the dbchecker container |
| dbchecker.securityContext | object | `{"allowPrivilegeEscalation":false,"runAsGroup":1001,"runAsNonRoot":true,"runAsUser":1001}` | SecurityContext for the dbchecker container |

### Frontend

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| frontend.env[0] | object | `{"name":"API_BASE_URL","value":"https://secobserve.dev/api"}` | Base URL for API |
| frontend.env[1] | object | `{"name":"OIDC_ENABLED","value":"false"}` | enable OIDC authentication |
| frontend.env[2] | object | `{"name":"OIDC_AUTHORITY","value":"https://oidc.secobserve.dev"}` | oidc metadata endpoint |
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

### Ingress

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| ingress.annotations | object | `{"kubernetes.io/ingress.class":"nginx","nginx.ingress.kubernetes.io/proxy-read-timeout":"600","nginx.ingress.kubernetes.io/proxy-send-timeout":"600","nginx.ingress.kubernetes.io/ssl-redirect":"true"}` | annotations to add to ingress |
| ingress.enabled | bool | `true` | If true, a Kubernetes Ingress resource will be created to the http port of the secobserve Service |
| ingress.hostname | string | `"secobserve.dev"` | hostname of ingress |
| ingress.ingressClassName | string | `"nginx"` | Example configuration for using an Amazon Load Balancer controller ingressClassName: alb annotations:   alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'   alb.ingress.kubernetes.io/ssl-policy: 'ELBSecurityPolicy-TLS13-1-2-FIPS-2023-04'   alb.ingress.kubernetes.io/healthcheck-path: / |

### Postgresql

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| postgresql.architecture | string | `"standalone"` | PostgreSQL architecture (`standalone` or `replication`) |
| postgresql.auth | object | `{"database":"secobserve","existingSecret":"","password":"","postgresPassword":"","secretKeys":{"userPasswordKey":"password"},"username":"secobserve"}` | enable postgresql subchart |
| postgresql.auth.database | string | `"secobserve"` | Name for a custom database to create |
| postgresql.auth.existingSecret | string | `""` | Name of existing secret to use for PostgreSQL credentials |
| postgresql.auth.password | string | `""` | Password for the custom user to create |
| postgresql.auth.postgresPassword | string | `""` | Password for the "postgres" admin user. Ignored if `auth.existingSecret` with key `postgres-password` is provided |
| postgresql.auth.secretKeys.userPasswordKey | string | `"password"` | Name of key in existing secret to use for PostgreSQL credentials. Only used when `auth.existingSecret` is set. |
| postgresql.auth.username | string | `"secobserve"` | Name for a custom user to create |
| postgresql.enabled | bool | `true` | Switch to enable or disable the PostgreSQL helm chart |
| postgresql.image | object | `{"repository":"bitnamilegacy/postgresql"}` | enable postgresql subchart |
| postgresql.metrics | object | `{"image":{"repository":"bitnamilegacy/postgres-exporter"}}` | enable postgresql subchart |
| postgresql.volumePermissions | object | `{"image":{"repository":"bitnamilegacy/os-shell"}}` | enable postgresql subchart |

### Service

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| service | object | `{"type":"ClusterIP"}` | defines the secobserve http service |
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
			<td>nodeSelector</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>Node labels to select for secobserve pod assignment</td>
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
  "name": "CORS_ALLOWED_ORIGINS",
  "value": "https://secobserve.dev"
}
</pre>
</td>
			<td>CORS allowed origins</td>
		</tr>
		<tr>
			<td>backend.env[11]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "DJANGO_SECRET_KEY",
  "valueFrom": {
    "secretKeyRef": {
      "key": "django_secret_key",
      "name": "secobserve-secrets"
    }
  }
}
</pre>
</td>
			<td>django secret key</td>
		</tr>
		<tr>
			<td>backend.env[11].valueFrom.secretKeyRef</td>
			<td>object</td>
			<td><pre lang="json">
{
  "key": "django_secret_key",
  "name": "secobserve-secrets"
}
</pre>
</td>
			<td>secret name containing the django secret key</td>
		</tr>
		<tr>
			<td>backend.env[12]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "FIELD_ENCRYPTION_KEY",
  "valueFrom": {
    "secretKeyRef": {
      "key": "field_encryption_key",
      "name": "secobserve-secrets"
    }
  }
}
</pre>
</td>
			<td>encryption key for fields</td>
		</tr>
		<tr>
			<td>backend.env[12].valueFrom.secretKeyRef</td>
			<td>object</td>
			<td><pre lang="json">
{
  "key": "field_encryption_key",
  "name": "secobserve-secrets"
}
</pre>
</td>
			<td>secret name containig the field encryption key</td>
		</tr>
		<tr>
			<td>backend.env[13]</td>
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
			<td>backend.env[14]</td>
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
			<td>backend.env[15]</td>
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
			<td>backend.env[16]</td>
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
			<td>backend.env[17]</td>
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
			<td>backend.env[18]</td>
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
			<td>backend.env[19]</td>
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
			<td>backend.env[1]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "ADMIN_PASSWORD",
  "valueFrom": {
    "secretKeyRef": {
      "key": "password",
      "name": "secobserve-secrets"
    }
  }
}
</pre>
</td>
			<td>admin password</td>
		</tr>
		<tr>
			<td>backend.env[20]</td>
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
			<td>backend.env[2]</td>
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
			<td>backend.env[3]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "DATABASE_ENGINE",
  "value": "django.db.backends.postgresql"
}
</pre>
</td>
			<td>database engine</td>
		</tr>
		<tr>
			<td>backend.env[4]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "DATABASE_HOST",
  "value": "secobserve-postgresql"
}
</pre>
</td>
			<td>database host/service</td>
		</tr>
		<tr>
			<td>backend.env[5]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "DATABASE_PORT",
  "value": "5432"
}
</pre>
</td>
			<td>database port</td>
		</tr>
		<tr>
			<td>backend.env[6]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "DATABASE_DB",
  "value": "secobserve"
}
</pre>
</td>
			<td>database name</td>
		</tr>
		<tr>
			<td>backend.env[7]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "DATABASE_USER",
  "value": "secobserve"
}
</pre>
</td>
			<td>database user</td>
		</tr>
		<tr>
			<td>backend.env[8]</td>
			<td>object</td>
			<td><pre lang="json">
{
  "name": "DATABASE_PASSWORD",
  "valueFrom": {
    "secretKeyRef": {
      "key": "password",
      "name": "secobserve-postgresql"
    }
  }
}
</pre>
</td>
			<td>database password</td>
		</tr>
		<tr>
			<td>backend.env[8].valueFrom.secretKeyRef</td>
			<td>object</td>
			<td><pre lang="json">
{
  "key": "password",
  "name": "secobserve-postgresql"
}
</pre>
</td>
			<td>reference to secret containing db credentials</td>
		</tr>
		<tr>
			<td>backend.env[9]</td>
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
			<td>security context to use for backend pod</td>
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
			<td>enable dbchecker init container</td>
		</tr>
		<tr>
			<td>dbchecker.hostname</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve-postgresql"
</pre>
</td>
			<td>enable dbchecker init container</td>
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
"latest"
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
			<td>enable dbchecker init container</td>
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
  "name": "OIDC_ENABLED",
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
			<td>oidc metadata endpoint</td>
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
			<td>Example configuration for using an Amazon Load Balancer controller ingressClassName: alb annotations:   alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'   alb.ingress.kubernetes.io/ssl-policy: 'ELBSecurityPolicy-TLS13-1-2-FIPS-2023-04'   alb.ingress.kubernetes.io/healthcheck-path: /</td>
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
			<td>enable postgresql subchart</td>
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
			<td>enable postgresql subchart</td>
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
			<td>enable postgresql subchart</td>
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
			<td>enable postgresql subchart</td>
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
  "type": "ClusterIP"
}
</pre>
</td>
			<td>defines the secobserve http service</td>
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
