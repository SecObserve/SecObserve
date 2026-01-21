# secobserve

![Version: 1.0.15](https://img.shields.io/badge/Version-1.0.15-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.47.1](https://img.shields.io/badge/AppVersion-1.47.1-informational?style=flat-square)

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

### Backend

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| backend.env | list | `[{"name":"ADMIN_USER","value":"admin"},{"name":"ADMIN_PASSWORD","valueFrom":{"secretKeyRef":{"key":"password","name":"secobserve-secrets"}}},{"name":"ADMIN_EMAIL","value":"admin@admin.com"},{"name":"DATABASE_ENGINE","value":"django.db.backends.postgresql"},{"name":"DATABASE_HOST","value":"secobserve-postgresql"},{"name":"DATABASE_PORT","value":"5432"},{"name":"DATABASE_DB","value":"secobserve"},{"name":"DATABASE_USER","value":"secobserve"},{"name":"DATABASE_PASSWORD","valueFrom":{"secretKeyRef":{"key":"password","name":"secobserve-postgresql"}}},{"name":"ALLOWED_HOSTS","value":"secobserve.dev"},{"name":"CORS_ALLOWED_ORIGINS","value":"https://secobserve.dev"},{"name":"DJANGO_SECRET_KEY","valueFrom":{"secretKeyRef":{"key":"django_secret_key","name":"secobserve-secrets"}}},{"name":"FIELD_ENCRYPTION_KEY","valueFrom":{"secretKeyRef":{"key":"field_encryption_key","name":"secobserve-secrets"}}},{"name":"OIDC_AUTHORITY","value":"https://oidc.secobserve.dev"},{"name":"OIDC_CLIENT_ID","value":"secobserve"},{"name":"OIDC_USERNAME","value":"preferred_username"},{"name":"OIDC_FIRST_NAME","value":"given_name"},{"name":"OIDC_LAST_NAME","value":"family_name"},{"name":"OIDC_FULL_NAME","value":"preferred_username"},{"name":"OIDC_EMAIL","value":"email"},{"name":"OIDC_GROUPS","value":"groups"}]` | environment configuration |
| backend.env[0].value | string | `"admin"` | admin user name |
| backend.env[10].value | string | `"https://secobserve.dev"` | CORS allowed origins |
| backend.env[11].valueFrom | object | `{"secretKeyRef":{"key":"django_secret_key","name":"secobserve-secrets"}}` | django secret key |
| backend.env[11].valueFrom.secretKeyRef | object | `{"key":"django_secret_key","name":"secobserve-secrets"}` | secret name containing the django secret key |
| backend.env[12].valueFrom | object | `{"secretKeyRef":{"key":"field_encryption_key","name":"secobserve-secrets"}}` | encryption key for fields |
| backend.env[12].valueFrom.secretKeyRef | object | `{"key":"field_encryption_key","name":"secobserve-secrets"}` | secret name containig the field encryption key |
| backend.env[13].value | string | `"https://oidc.secobserve.dev"` | admin OIDC authority |
| backend.env[14].value | string | `"secobserve"` | OIDC client id |
| backend.env[15].value | string | `"preferred_username"` | OIDC user name |
| backend.env[16].value | string | `"given_name"` | OIDC first name |
| backend.env[17].value | string | `"family_name"` | OIDC last name |
| backend.env[18].value | string | `"preferred_username"` | OIDC full name |
| backend.env[19].value | string | `"email"` | OIDC email address |
| backend.env[1].valueFrom.secretKeyRef | object | `{"key":"password","name":"secobserve-secrets"}` | reference to secret to get the admin password |
| backend.env[20].value | string | `"groups"` | OIDC groups |
| backend.env[2].value | string | `"admin@admin.com"` | admin email address |
| backend.env[3].value | string | `"django.db.backends.postgresql"` | database engine |
| backend.env[4].value | string | `"secobserve-postgresql"` | database host/service |
| backend.env[5].value | string | `"5432"` | database port |
| backend.env[6].value | string | `"secobserve"` | database name |
| backend.env[7].value | string | `"secobserve"` | database user |
| backend.env[8].valueFrom.secretKeyRef | object | `{"key":"password","name":"secobserve-postgresql"}` | reference to secret containing db credentials |
| backend.env[9].value | string | `"secobserve.dev"` | allowed hosts |
| backend.image | object | `{"pullPolicy":"IfNotPresent","registry":"ghcr.io","repository":"secobserve/secobserve-backend","tag":null}` | image registry |
| backend.image.pullPolicy | string | `"IfNotPresent"` | image pull policy |
| backend.image.repository | string | `"secobserve/secobserve-backend"` | image repository |
| backend.image.tag | string | `nil` | image tag @default {{ .Charts.AppVersion}} |
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
| frontend.env | list | `[{"name":"API_BASE_URL","value":"https://secobserve.dev/api"},{"name":"OIDC_ENABLED","value":"false"},{"name":"OIDC_AUTHORITY","value":"https://oidc.secobserve.dev"},{"name":"OIDC_CLIENT_ID","value":"secobserve"},{"name":"OIDC_REDIRECT_URI","value":"https://secobserve.dev/"},{"name":"OIDC_POST_LOGOUT_REDIRECT_URI","value":"https://secobserve.dev/"},{"name":"OIDC_PROMPT","value":null}]` | Frontend environment variables |
| frontend.env[0] | object | `{"name":"API_BASE_URL","value":"https://secobserve.dev/api"}` | Base URL for API |
| frontend.image.pullPolicy | string | `"IfNotPresent"` | image pull policy |
| frontend.image.registry | string | `"ghcr.io"` | image registry |
| frontend.image.repository | string | `"secobserve/secobserve-frontend"` | image repository |
| frontend.image.tag | string | (chart/appVersion) | image tag |
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

### Service

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| service | object | `{"type":"ClusterIP"}` | defines the secobserve http service |
| service.type | string | `"ClusterIP"` | Service type of service |

### Other Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` |  |
| backend.env[0].name | string | `"ADMIN_USER"` |  |
| backend.env[0].value | string | `"admin"` |  |
| backend.env[10].name | string | `"CORS_ALLOWED_ORIGINS"` |  |
| backend.env[10].value | string | `"https://secobserve.dev"` |  |
| backend.env[11].name | string | `"DJANGO_SECRET_KEY"` |  |
| backend.env[11].valueFrom.secretKeyRef.key | string | `"django_secret_key"` |  |
| backend.env[11].valueFrom.secretKeyRef.name | string | `"secobserve-secrets"` |  |
| backend.env[12].name | string | `"FIELD_ENCRYPTION_KEY"` |  |
| backend.env[12].valueFrom.secretKeyRef.key | string | `"field_encryption_key"` |  |
| backend.env[12].valueFrom.secretKeyRef.name | string | `"secobserve-secrets"` |  |
| backend.env[13].name | string | `"OIDC_AUTHORITY"` |  |
| backend.env[13].value | string | `"https://oidc.secobserve.dev"` |  |
| backend.env[14].name | string | `"OIDC_CLIENT_ID"` |  |
| backend.env[14].value | string | `"secobserve"` |  |
| backend.env[15].name | string | `"OIDC_USERNAME"` |  |
| backend.env[15].value | string | `"preferred_username"` |  |
| backend.env[16].name | string | `"OIDC_FIRST_NAME"` |  |
| backend.env[16].value | string | `"given_name"` |  |
| backend.env[17].name | string | `"OIDC_LAST_NAME"` |  |
| backend.env[17].value | string | `"family_name"` |  |
| backend.env[18].name | string | `"OIDC_FULL_NAME"` |  |
| backend.env[18].value | string | `"preferred_username"` |  |
| backend.env[19].name | string | `"OIDC_EMAIL"` |  |
| backend.env[19].value | string | `"email"` |  |
| backend.env[1].name | string | `"ADMIN_PASSWORD"` |  |
| backend.env[1].valueFrom.secretKeyRef.key | string | `"password"` |  |
| backend.env[1].valueFrom.secretKeyRef.name | string | `"secobserve-secrets"` |  |
| backend.env[20].name | string | `"OIDC_GROUPS"` |  |
| backend.env[20].value | string | `"groups"` |  |
| backend.env[2].name | string | `"ADMIN_EMAIL"` |  |
| backend.env[2].value | string | `"admin@admin.com"` |  |
| backend.env[3].name | string | `"DATABASE_ENGINE"` |  |
| backend.env[3].value | string | `"django.db.backends.postgresql"` |  |
| backend.env[4].name | string | `"DATABASE_HOST"` |  |
| backend.env[4].value | string | `"secobserve-postgresql"` |  |
| backend.env[5].name | string | `"DATABASE_PORT"` |  |
| backend.env[5].value | string | `"5432"` |  |
| backend.env[6].name | string | `"DATABASE_DB"` |  |
| backend.env[6].value | string | `"secobserve"` |  |
| backend.env[7].name | string | `"DATABASE_USER"` |  |
| backend.env[7].value | string | `"secobserve"` |  |
| backend.env[8].name | string | `"DATABASE_PASSWORD"` |  |
| backend.env[8].valueFrom.secretKeyRef.key | string | `"password"` |  |
| backend.env[8].valueFrom.secretKeyRef.name | string | `"secobserve-postgresql"` |  |
| backend.env[9].name | string | `"ALLOWED_HOSTS"` |  |
| backend.env[9].value | string | `"secobserve.dev"` |  |
| backend.image.pullPolicy | string | `"IfNotPresent"` |  |
| backend.image.registry | string | `"docker.io"` |  |
| backend.image.repository | string | `"ghcr.io/secobserve/secobserve-backend"` |  |
| backend.image.tag | string | `"1.47.2"` |  |
| backend.resources.limits.cpu | string | `"1000m"` |  |
| backend.resources.limits.memory | string | `"1500Mi"` |  |
| backend.resources.requests.cpu | string | `"1000m"` |  |
| backend.resources.requests.memory | string | `"1500Mi"` |  |
| backend.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| backend.securityContext.enabled | bool | `true` |  |
| backend.securityContext.runAsGroup | int | `1001` |  |
| backend.securityContext.runAsNonRoot | bool | `true` |  |
| backend.securityContext.runAsUser | int | `1001` |  |
| backend.service.port | int | `5000` |  |
| dbchecker.enabled | bool | `true` |  |
| dbchecker.hostname | string | `"secobserve-postgresql"` |  |
| dbchecker.image.pullPolicy | string | `"IfNotPresent"` |  |
| dbchecker.image.repository | string | `"busybox"` |  |
| dbchecker.image.tag | string | `"latest"` |  |
| dbchecker.port | int | `5432` |  |
| dbchecker.resources.limits.cpu | string | `"20m"` |  |
| dbchecker.resources.limits.memory | string | `"32Mi"` |  |
| dbchecker.resources.requests.cpu | string | `"20m"` |  |
| dbchecker.resources.requests.memory | string | `"32Mi"` |  |
| dbchecker.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| dbchecker.securityContext.runAsGroup | int | `1000` |  |
| dbchecker.securityContext.runAsNonRoot | bool | `true` |  |
| dbchecker.securityContext.runAsUser | int | `1000` |  |
| frontend.env[0].name | string | `"API_BASE_URL"` |  |
| frontend.env[0].value | string | `"https://secobserve.dev/api"` |  |
| frontend.env[1].name | string | `"OIDC_ENABLED"` |  |
| frontend.env[1].value | string | `"false"` |  |
| frontend.env[2].name | string | `"OIDC_AUTHORITY"` |  |
| frontend.env[2].value | string | `"https://oidc.secobserve.dev"` |  |
| frontend.env[3].name | string | `"OIDC_CLIENT_ID"` |  |
| frontend.env[3].value | string | `"secobserve"` |  |
| frontend.env[4].name | string | `"OIDC_REDIRECT_URI"` |  |
| frontend.env[4].value | string | `"https://secobserve.dev/"` |  |
| frontend.env[5].name | string | `"OIDC_POST_LOGOUT_REDIRECT_URI"` |  |
| frontend.env[5].value | string | `"https://secobserve.dev/"` |  |
| frontend.env[5].name | string | `"OIDC_PROMPT"` |  |
| frontend.env[5].value | string | null |  |
| frontend.image.pullPolicy | string | `"IfNotPresent"` |  |
| frontend.image.registry | string | `"docker.io"` |  |
| frontend.image.repository | string | `"ghcr.io/secobserve/secobserve-frontend"` |  |
| frontend.image.tag | string | `"1.47.2"` |  |
| frontend.resources.limits.cpu | string | `"500m"` |  |
| frontend.resources.limits.memory | string | `"1000Mi"` |  |
| frontend.resources.requests.cpu | string | `"500m"` |  |
| frontend.resources.requests.memory | string | `"1000Mi"` |  |
| frontend.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| frontend.securityContext.enabled | bool | `true` |  |
| frontend.securityContext.runAsGroup | int | `101` |  |
| frontend.securityContext.runAsNonRoot | bool | `true` |  |
| frontend.securityContext.runAsUser | int | `101` |  |
| frontend.service.port | int | `3000` |  |
| ingress.annotations."kubernetes.io/ingress.class" | string | `"nginx"` |  |
| ingress.annotations."nginx.ingress.kubernetes.io/proxy-read-timeout" | string | `"600"` |  |
| ingress.annotations."nginx.ingress.kubernetes.io/proxy-send-timeout" | string | `"600"` |  |
| ingress.annotations."nginx.ingress.kubernetes.io/ssl-redirect" | string | `"true"` |  |
| ingress.enabled | bool | `true` |  |
| ingress.hostname | string | `"secobserve.dev"` |  |
| ingress.ingressClassName | string | `"nginx"` |  |
| nodeSelector | object | `{}` |  |
| postgresql.architecture | string | `"standalone"` |  |
| postgresql.auth.database | string | `"secobserve"` |  |
| postgresql.auth.existingSecret | string | `""` |  |
| postgresql.auth.password | string | `""` |  |
| postgresql.auth.postgresPassword | string | `""` |  |
| postgresql.auth.secretKeys.userPasswordKey | string | `"password"` |  |
| postgresql.auth.username | string | `"secobserve"` |  |
| postgresql.enabled | bool | `true` | enable postgresql subchart |
| postgresql.image.repository | string | `"bitnamilegacy/postgresql"` |  |
| postgresql.metrics.image.repository | string | `"bitnamilegacy/postgres-exporter"` |  |
| postgresql.volumePermissions.image.repository | string | `"bitnamilegacy/os-shell"` |  |
| replicaCount | int | `1` |  |
| tolerations | object | `{}` | Toleration labels for pod assignment |

## Values

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
			<td>backend.env</td>
			<td>list</td>
			<td><pre lang="json">
[
  {
    "name": "ADMIN_USER",
    "value": "admin"
  },
  {
    "name": "ADMIN_PASSWORD",
    "valueFrom": {
      "secretKeyRef": {
        "key": "password",
        "name": "secobserve-secrets"
      }
    }
  },
  {
    "name": "ADMIN_EMAIL",
    "value": "admin@admin.com"
  },
  {
    "name": "DATABASE_ENGINE",
    "value": "django.db.backends.postgresql"
  },
  {
    "name": "DATABASE_HOST",
    "value": "secobserve-postgresql"
  },
  {
    "name": "DATABASE_PORT",
    "value": "5432"
  },
  {
    "name": "DATABASE_DB",
    "value": "secobserve"
  },
  {
    "name": "DATABASE_USER",
    "value": "secobserve"
  },
  {
    "name": "DATABASE_PASSWORD",
    "valueFrom": {
      "secretKeyRef": {
        "key": "password",
        "name": "secobserve-postgresql"
      }
    }
  },
  {
    "name": "ALLOWED_HOSTS",
    "value": "secobserve.dev"
  },
  {
    "name": "CORS_ALLOWED_ORIGINS",
    "value": "https://secobserve.dev"
  },
  {
    "name": "DJANGO_SECRET_KEY",
    "valueFrom": {
      "secretKeyRef": {
        "key": "django_secret_key",
        "name": "secobserve-secrets"
      }
    }
  },
  {
    "name": "FIELD_ENCRYPTION_KEY",
    "valueFrom": {
      "secretKeyRef": {
        "key": "field_encryption_key",
        "name": "secobserve-secrets"
      }
    }
  },
  {
    "name": "OIDC_AUTHORITY",
    "value": "https://oidc.secobserve.dev"
  },
  {
    "name": "OIDC_CLIENT_ID",
    "value": "secobserve"
  },
  {
    "name": "OIDC_USERNAME",
    "value": "preferred_username"
  },
  {
    "name": "OIDC_FIRST_NAME",
    "value": "given_name"
  },
  {
    "name": "OIDC_LAST_NAME",
    "value": "family_name"
  },
  {
    "name": "OIDC_FULL_NAME",
    "value": "preferred_username"
  },
  {
    "name": "OIDC_EMAIL",
    "value": "email"
  },
  {
    "name": "OIDC_GROUPS",
    "value": "groups"
  }
]
</pre>
</td>
			<td>environment configuration</td>
		</tr>
		<tr>
			<td>backend.env[0].value</td>
			<td>string</td>
			<td><pre lang="json">
"admin"
</pre>
</td>
			<td>admin user name</td>
		</tr>
		<tr>
			<td>backend.env[10].value</td>
			<td>string</td>
			<td><pre lang="json">
"https://secobserve.dev"
</pre>
</td>
			<td>CORS allowed origins</td>
		</tr>
		<tr>
			<td>backend.env[11].valueFrom</td>
			<td>object</td>
			<td><pre lang="json">
{
  "secretKeyRef": {
    "key": "django_secret_key",
    "name": "secobserve-secrets"
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
			<td>backend.env[12].valueFrom</td>
			<td>object</td>
			<td><pre lang="json">
{
  "secretKeyRef": {
    "key": "field_encryption_key",
    "name": "secobserve-secrets"
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
			<td>backend.env[13].value</td>
			<td>string</td>
			<td><pre lang="json">
"https://oidc.secobserve.dev"
</pre>
</td>
			<td>admin OIDC authority</td>
		</tr>
		<tr>
			<td>backend.env[14].value</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve"
</pre>
</td>
			<td>OIDC client id</td>
		</tr>
		<tr>
			<td>backend.env[15].value</td>
			<td>string</td>
			<td><pre lang="json">
"preferred_username"
</pre>
</td>
			<td>OIDC user name</td>
		</tr>
		<tr>
			<td>backend.env[16].value</td>
			<td>string</td>
			<td><pre lang="json">
"given_name"
</pre>
</td>
			<td>OIDC first name</td>
		</tr>
		<tr>
			<td>backend.env[17].value</td>
			<td>string</td>
			<td><pre lang="json">
"family_name"
</pre>
</td>
			<td>OIDC last name</td>
		</tr>
		<tr>
			<td>backend.env[18].value</td>
			<td>string</td>
			<td><pre lang="json">
"preferred_username"
</pre>
</td>
			<td>OIDC full name</td>
		</tr>
		<tr>
			<td>backend.env[19].value</td>
			<td>string</td>
			<td><pre lang="json">
"email"
</pre>
</td>
			<td>OIDC email address</td>
		</tr>
		<tr>
			<td>backend.env[1].valueFrom.secretKeyRef</td>
			<td>object</td>
			<td><pre lang="json">
{
  "key": "password",
  "name": "secobserve-secrets"
}
</pre>
</td>
			<td>reference to secret to get the admin password</td>
		</tr>
		<tr>
			<td>backend.env[20].value</td>
			<td>string</td>
			<td><pre lang="json">
"groups"
</pre>
</td>
			<td>OIDC groups</td>
		</tr>
		<tr>
			<td>backend.env[2].value</td>
			<td>string</td>
			<td><pre lang="json">
"admin@admin.com"
</pre>
</td>
			<td>admin email address</td>
		</tr>
		<tr>
			<td>backend.env[3].value</td>
			<td>string</td>
			<td><pre lang="json">
"django.db.backends.postgresql"
</pre>
</td>
			<td>database engine</td>
		</tr>
		<tr>
			<td>backend.env[4].value</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve-postgresql"
</pre>
</td>
			<td>database host/service</td>
		</tr>
		<tr>
			<td>backend.env[5].value</td>
			<td>string</td>
			<td><pre lang="json">
"5432"
</pre>
</td>
			<td>database port</td>
		</tr>
		<tr>
			<td>backend.env[6].value</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve"
</pre>
</td>
			<td>database name</td>
		</tr>
		<tr>
			<td>backend.env[7].value</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve"
</pre>
</td>
			<td>database user</td>
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
			<td>backend.env[9].value</td>
			<td>string</td>
			<td><pre lang="json">
"secobserve.dev"
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
			<td>image tag @default {{ .Charts.AppVersion}}</td>
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
			<td>frontend.env</td>
			<td>list</td>
			<td><pre lang="json">
[
  {
    "name": "API_BASE_URL",
    "value": "https://secobserve.dev/api"
  },
  {
    "name": "OIDC_ENABLED",
    "value": "false"
  },
  {
    "name": "OIDC_AUTHORITY",
    "value": "https://oidc.secobserve.dev"
  },
  {
    "name": "OIDC_CLIENT_ID",
    "value": "secobserve"
  },
  {
    "name": "OIDC_REDIRECT_URI",
    "value": "https://secobserve.dev/"
  },
  {
    "name": "OIDC_POST_LOGOUT_REDIRECT_URI",
    "value": "https://secobserve.dev/"
  },
  {
    "name": "OIDC_PROMPT",
    "value": null
  }
]
</pre>
</td>
			<td>Frontend environment variables</td>
		</tr>
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
			<td><pre lang="">
(chart/appVersion)
</pre>
</td>
			<td>image tag</td>
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

<h3>Other Values</h3>
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
		<td>nodeSelector</td>
		<td>object</td>
		<td><pre lang="json">
{}
</pre>
</td>
		<td>Node labels for secobserve pod assignment</td>
	</tr>
	<tr>
		<td>postgresql.architecture</td>
		<td>string</td>
		<td><pre lang="json">
"standalone"
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.auth.database</td>
		<td>string</td>
		<td><pre lang="json">
"secobserve"
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.auth.existingSecret</td>
		<td>string</td>
		<td><pre lang="json">
""
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.auth.password</td>
		<td>string</td>
		<td><pre lang="json">
""
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.auth.postgresPassword</td>
		<td>string</td>
		<td><pre lang="json">
""
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.auth.secretKeys.userPasswordKey</td>
		<td>string</td>
		<td><pre lang="json">
"password"
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.auth.username</td>
		<td>string</td>
		<td><pre lang="json">
"secobserve"
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.enabled</td>
		<td>bool</td>
		<td><pre lang="json">
true
</pre>
</td>
		<td>enable postgresql subchart</td>
	</tr>
	<tr>
		<td>postgresql.image.repository</td>
		<td>string</td>
		<td><pre lang="json">
"bitnamilegacy/postgresql"
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.metrics.image.repository</td>
		<td>string</td>
		<td><pre lang="json">
"bitnamilegacy/postgres-exporter"
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>postgresql.volumePermissions.image.repository</td>
		<td>string</td>
		<td><pre lang="json">
"bitnamilegacy/os-shell"
</pre>
</td>
		<td></td>
	</tr>
	<tr>
		<td>replicaCount</td>
		<td>int</td>
		<td><pre lang="json">
1
</pre>
</td>
		<td></td>
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

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
