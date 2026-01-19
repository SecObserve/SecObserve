# secobserve

![Version: 2.0.0](https://img.shields.io/badge/Version-2.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.47.1](https://img.shields.io/badge/AppVersion-1.47.1-informational?style=flat-square)

A Helm chart to deploy SecObserve, an open-source vulnerability and license management system designed for software development teams and cloud-native environments. SecObserve helps teams identify, manage, and remediate security vulnerabilities and license compliance issues across their software projects, enhancing visibility and improving DevSecOps workflows.

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

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | Sets the affinity for the secobserve pod For more information on affinity, see https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity |
| backend.env[0] | object | `{"name":"ADMIN_EMAIL","value":"admin@admin.com"}` | Email address of the admin user |
| backend.env[10].name | string | `"OIDC_GROUPS"` |  |
| backend.env[10].value | string | `"groups"` |  |
| backend.env[1].name | string | `"ALLOWED_HOSTS"` |  |
| backend.env[1].value | string | `"secobserve.dev"` |  |
| backend.env[2].name | string | `"CORS_ALLOWED_ORIGINS"` |  |
| backend.env[2].value | string | `"https://secobserve.dev"` |  |
| backend.env[3] | object | `{"name":"OIDC_AUTHORITY","value":"https://oidc.secobserve.dev"}` | OIDC authority |
| backend.env[4] | object | `{"name":"OIDC_CLIENT_ID","value":"secobserve"}` | OIDC client ID |
| backend.env[5] | object | `{"name":"OIDC_USERNAME","value":"preferred_username"}` | OIDC user name |
| backend.env[6] | object | `{"name":"OIDC_FIRST_NAME","value":"given_name"}` | OIDC first name |
| backend.env[7] | object | `{"name":"OIDC_LAST_NAME","value":"family_name"}` | OIDC last name |
| backend.env[8] | object | `{"name":"OIDC_FULL_NAME","value":"preferred_username"}` | OIDC full name |
| backend.env[9] | object | `{"name":"OIDC_EMAIL","value":"email"}` | OIDC email |
| backend.image | object | `{"pullPolicy":"IfNotPresent","registry":"ghcr.io","repository":"secobserve/secobserve-backend","tag":null}` | backend image |
| backend.image.pullPolicy | string | `"IfNotPresent"` | image pull policy |
| backend.image.registry | string | `"ghcr.io"` | registry to use for the frontend image |
| backend.image.repository | string | `"secobserve/secobserve-backend"` | backend image repository |
| backend.image.tag | string | {{ .Chart.AppVersion }} | Tag to use for image |
| backend.resources | object | `{"limits":{"cpu":"1000m","memory":"1500Mi"},"requests":{"cpu":"1000m","memory":"1500Mi"}}` | resource requirements and limits |
| backend.securityContext | object | `{"allowPrivilegeEscalation":false,"runAsGroup":1001,"runAsNonRoot":true,"runAsUser":1001}` | backend container security context |
| backend.service | object | `{"port":5000}` | service port |
| databaseSecretName | string | `""` | Database secret name is required if the postgres subchart is disabled |
| dbchecker.enabled | bool | `true` |  |
| dbchecker.hostname | string | `nil` |  |
| dbchecker.image.pullPolicy | string | `"IfNotPresent"` | Image pull policy for the dbchecker image |
| dbchecker.image.repository | string | `"busybox"` | Docker image used to check Database readiness at startup |
| dbchecker.image.tag | string | `"latest"` | Image tag for the dbchecker image |
| dbchecker.port | int | `5432` |  |
| dbchecker.resources | object | `{"limits":{"cpu":"20m","memory":"32Mi"},"requests":{"cpu":"20m","memory":"32Mi"}}` | Resource requests and limits for the dbchecker container |
| dbchecker.securityContext | object | `{"allowPrivilegeEscalation":false,"runAsGroup":1001,"runAsNonRoot":true,"runAsUser":1001}` | SecurityContext for the dbchecker container |
| frontend.env[0] | object | `{"name":"API_BASE_URL","value":"https://secobserve.dev/api"}` | API base URL |
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
| frontend.env[6].name | string | `"OIDC_PROMPT"` |  |
| frontend.env[6].value | string | `nil` |  |
| frontend.image | object | `{"pullPolicy":"IfNotPresent","registry":"ghcr.io","repository":"secobserve/secobserve-frontend","tag":null}` | image to use |
| frontend.image.pullPolicy | string | `"IfNotPresent"` | image pull policy |
| frontend.image.registry | string | `"ghcr.io"` | registry to use for the frontend image |
| frontend.image.repository | string | `"secobserve/secobserve-frontend"` | image repository |
| frontend.image.tag | string | {{ .Chart.AppVersion }} | Tag to use for image |
| frontend.resources.limits.cpu | string | `"500m"` |  |
| frontend.resources.limits.memory | string | `"1000Mi"` |  |
| frontend.resources.requests.cpu | string | `"500m"` |  |
| frontend.resources.requests.memory | string | `"1000Mi"` |  |
| frontend.securityContext | object | `{"allowPrivilegeEscalation":false,"runAsGroup":1001,"runAsNonRoot":true,"runAsUser":1001}` | frontend container security context |
| frontend.service | object | `{"port":3000}` | service configuration |
| ingress.annotations."kubernetes.io/ingress.class" | string | `"nginx"` |  |
| ingress.annotations."nginx.ingress.kubernetes.io/proxy-read-timeout" | string | `"600"` |  |
| ingress.annotations."nginx.ingress.kubernetes.io/proxy-send-timeout" | string | `"600"` |  |
| ingress.annotations."nginx.ingress.kubernetes.io/ssl-redirect" | string | `"true"` |  |
| ingress.enabled | bool | `true` | enable the ingress definition If true, a Kubernetes Ingress resource will be created to the http port of the secobserve Service |
| ingress.hostname | string | `"secobserve.dev"` |  |
| ingress.ingressClassName | string | `"nginx"` |  |
| nodeSelector | object | `{}` | Node labels for secobserve pod assignment |
| postgresql.architecture | string | `"standalone"` |  |
| postgresql.auth.database | string | `"secobserve"` |  |
| postgresql.auth.existingSecret | string | `""` |  |
| postgresql.auth.password | string | `""` |  |
| postgresql.auth.postgresPassword | string | `""` |  |
| postgresql.auth.secretKeys.userPasswordKey | string | `"password"` |  |
| postgresql.auth.username | string | `"secobserve"` |  |
| postgresql.enabled | bool | `true` | enables the bitnami postgres subchart if `true` |
| postgresql.image.repository | string | `"bitnamilegacy/postgresql"` |  |
| postgresql.metrics.image.repository | string | `"bitnamilegacy/postgres-exporter"` |  |
| postgresql.volumePermissions.image.repository | string | `"bitnamilegacy/os-shell"` |  |
| replicaCount | int | `1` |  |
| secobserveSecret | object | `{"adminPassword":"","adminUser":"admin","existingSecret":""}` | defines the generated secret for secobserve. Will only be generated if the secret does not exist yet |
| secobserveSecret.adminPassword | string | `""` | An empty adminPasword will generate a random password |
| secobserveSecret.adminUser | string | `"admin"` | Username for the admin user |
| secobserveSecret.existingSecret | string | `""` | Specify the name of an existing secret. Disables generation of the default secret |
| service | object | `{"type":"ClusterIP"}` | Defines the secobserve http service |
| tolerations | object | `{}` | Toleration labels for pod assignment |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
