{{/*
Expand the name of the chart.
*/}}
{{- define "secobserve.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "secobserve.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := include "secobserve.name" . -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Mirror the Bitnami PostgreSQL subchart's fullname logic so the application can
refer to the generated Service and Secret without hard-coding the release name.
*/}}
{{- define "secobserve.postgresql.fullname" -}}
{{- $globalFullnameOverride := "" -}}
{{- with .Values.global -}}
{{- with .postgresql -}}
{{- $globalFullnameOverride = default "" .fullnameOverride -}}
{{- end -}}
{{- end -}}
{{- if $globalFullnameOverride -}}
{{- $globalFullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else if .Values.postgresql.fullnameOverride -}}
{{- .Values.postgresql.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default "postgresql" .Values.postgresql.nameOverride -}}
{{- $releaseName := regexReplaceAll "(-?[^a-z\\d\\-])+-?" (lower .Release.Name) "-" -}}
{{- if contains $name $releaseName -}}
{{- $releaseName | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" $releaseName $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/* Return the PostgreSQL primary Service name. */}}
{{- define "secobserve.postgresql.primaryFullname" -}}
{{- $fullname := include "secobserve.postgresql.fullname" . -}}
{{- if eq .Values.postgresql.architecture "replication" -}}
{{- printf "%s-%s" $fullname (default "primary" .Values.postgresql.primary.name) | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $fullname -}}
{{- end -}}
{{- end -}}

{{/* Return the configured database host or the bundled PostgreSQL primary Service. */}}
{{- define "secobserve.databaseHost" -}}
{{- if .Values.database.host -}}
{{- .Values.database.host -}}
{{- else if .Values.postgresql.enabled -}}
{{- include "secobserve.postgresql.primaryFullname" . -}}
{{- else -}}
{{- required "database.host is required when postgresql.enabled is false" .Values.database.host -}}
{{- end -}}
{{- end -}}

{{/* Return the Secret containing the application database password. */}}
{{- define "secobserve.databaseSecretName" -}}
{{- if .Values.database.passwordSecret.name -}}
{{- .Values.database.passwordSecret.name -}}
{{- else if .Values.postgresql.auth.existingSecret -}}
{{- .Values.postgresql.auth.existingSecret -}}
{{- else if .Values.postgresql.enabled -}}
{{- include "secobserve.postgresql.fullname" . -}}
{{- else -}}
{{- required "database.passwordSecret.name is required when postgresql.enabled is false" .Values.database.passwordSecret.name -}}
{{- end -}}
{{- end -}}

{{/* Return the key containing the application database password. */}}
{{- define "secobserve.databaseSecretKey" -}}
{{- if .Values.database.passwordSecret.key -}}
{{- .Values.database.passwordSecret.key -}}
{{- else if .Values.postgresql.auth.existingSecret -}}
{{- .Values.postgresql.auth.secretKeys.userPasswordKey -}}
{{- else -}}
password
{{- end -}}
{{- end -}}

{{/* Return the database engine; the last backend.env DATABASE_ENGINE entry with a value wins. */}}
{{- define "secobserve.databaseEngine" -}}
{{- $engine := .Values.database.engine -}}
{{- range .Values.backend.env -}}
{{- if and (eq .name "DATABASE_ENGINE") (hasKey . "value") -}}
{{- $engine = .value -}}
{{- end -}}
{{- end -}}
{{- $engine -}}
{{- end -}}

{{/* Return the PVC used for the Huey SQLite queue. */}}
{{- define "secobserve.huey.claimName" -}}
{{- default (printf "%s-huey" (include "secobserve.fullname" .) | trunc 63 | trimSuffix "-") .Values.huey.persistence.existingClaim -}}
{{- end -}}

{{/* Return the Secret containing SecObserve application secrets. */}}
{{- define "secobserve.secretName" -}}
{{- default (printf "%s-secrets" (include "secobserve.fullname" .) | trunc 63 | trimSuffix "-") .Values.backend.existingSecret -}}
{{- end -}}

{{/*
Render backend environment variables. Entries explicitly supplied through
backend.env take precedence, preserving compatibility with older values files.
*/}}
{{- define "secobserve.backendEnv" -}}
{{- $configuredNames := dict -}}
{{- range .Values.backend.env -}}
{{- $_ := set $configuredNames .name true -}}
{{- end -}}
{{- if not (hasKey $configuredNames "ADMIN_PASSWORD") }}
- name: ADMIN_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "secobserve.secretName" . }}
      key: {{ .Values.backend.secretKeys.adminPassword }}
{{- end }}
{{- if not (hasKey $configuredNames "DATABASE_ENGINE") }}
- name: DATABASE_ENGINE
  value: {{ .Values.database.engine | quote }}
{{- end }}
{{- if not (hasKey $configuredNames "DATABASE_HOST") }}
- name: DATABASE_HOST
  value: {{ include "secobserve.databaseHost" . | quote }}
{{- end }}
{{- if not (hasKey $configuredNames "DATABASE_PORT") }}
- name: DATABASE_PORT
  value: {{ .Values.database.port | quote }}
{{- end }}
{{- if not (hasKey $configuredNames "DATABASE_DB") }}
- name: DATABASE_DB
  value: {{ default .Values.postgresql.auth.database .Values.database.name | quote }}
{{- end }}
{{- if not (hasKey $configuredNames "DATABASE_USER") }}
- name: DATABASE_USER
  value: {{ default .Values.postgresql.auth.username .Values.database.username | quote }}
{{- end }}
{{- if not (hasKey $configuredNames "DATABASE_PASSWORD") }}
- name: DATABASE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "secobserve.databaseSecretName" . }}
      key: {{ include "secobserve.databaseSecretKey" . }}
{{- end }}
{{- if not (hasKey $configuredNames "DJANGO_SECRET_KEY") }}
- name: DJANGO_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "secobserve.secretName" . }}
      key: {{ .Values.backend.secretKeys.djangoSecretKey }}
{{- end }}
{{- if not (hasKey $configuredNames "FIELD_ENCRYPTION_KEY") }}
- name: FIELD_ENCRYPTION_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "secobserve.secretName" . }}
      key: {{ .Values.backend.secretKeys.fieldEncryptionKey }}
{{- end }}
{{- with .Values.backend.env }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "secobserve.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "secobserve.labels" -}}
helm.sh/chart: {{ include "secobserve.chart" . }}
{{ include "secobserve.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "secobserve.selectorLabels" -}}
com.secobserve.tenant: {{ include "secobserve.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Selector labels for a single component. Call with a dict, for example:
{{ include "secobserve.componentSelectorLabels" (dict "context" $ "component" "api") }}
*/}}
{{- define "secobserve.componentSelectorLabels" -}}
{{ include "secobserve.selectorLabels" .context }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/* Return the name of the Service exposing the frontend. */}}
{{- define "secobserve.frontendServiceName" -}}
{{- if eq (default "single" .Values.architecture) "ha" -}}
{{- printf "%s-frontend-svc" (include "secobserve.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-svc" (include "secobserve.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/* Return the name of the Service exposing the backend API. */}}
{{- define "secobserve.backendServiceName" -}}
{{- if eq (default "single" .Values.architecture) "ha" -}}
{{- printf "%s-backend-svc" (include "secobserve.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-svc" (include "secobserve.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/* Init container waiting for the database to accept connections. */}}
{{- define "secobserve.dbcheckerInitContainer" -}}
- name: dbchecker
  image: "{{ .Values.dbchecker.image.repository }}{{- if (.Values.dbchecker.image.digest) -}}@{{ .Values.dbchecker.image.digest }}{{- else -}}:{{ .Values.dbchecker.image.tag }} {{- end }}"
  imagePullPolicy: {{ .Values.dbchecker.image.pullPolicy }}
  {{- if .Values.dbchecker.securityContext.enabled }}
  securityContext:
    {{- omit .Values.dbchecker.securityContext "enabled" | toYaml | nindent 4 }}
  {{- end }}
  command:
    - sh
    - -c
    - |
      echo 'Waiting for Database to become ready...'

      until printf "." && nc -z -w 2 {{ default (include "secobserve.databaseHost" .) .Values.dbchecker.hostname }} {{ default .Values.database.port .Values.dbchecker.port }}; do
          sleep 2;
      done;

      echo 'Database OK ✓'
  resources:
    {{- toYaml .Values.dbchecker.resources | nindent 4 }}
{{- end -}}

{{/*
Image reference, by digest when one is set. Call with a dict, for example:
{{ include "secobserve.image" (dict "image" .Values.backend.image "context" $) }}
*/}}
{{- define "secobserve.image" -}}
{{- if .image.digest -}}
{{- printf "%s/%s@%s" .image.registry .image.repository .image.digest -}}
{{- else -}}
{{- printf "%s/%s:%v" .image.registry .image.repository (.image.tag | default .context.Chart.AppVersion) -}}
{{- end -}}
{{- end -}}

{{/*
Resources of a backend component, falling back to backend.resources when empty. Call with a dict, for example:
{{ include "secobserve.backendResources" (dict "context" $ "resources" .Values.backend.api.resources) }}
*/}}
{{- define "secobserve.backendResources" -}}
{{- toYaml (default .context.Values.backend.resources .resources) -}}
{{- end -}}

{{/*
Init container waiting for the init Job to have applied all migrations. Uses the
backend image, so no additional image has to be pulled. Call with a dict of
"context" and the "resources" of the component the Pod belongs to.
*/}}
{{- define "secobserve.migrationsInitContainer" -}}
- name: wait-for-migrations
  image: "{{ include "secobserve.image" (dict "image" .context.Values.backend.image "context" .context) }}"
  imagePullPolicy: {{ .context.Values.backend.image.pullPolicy }}
  {{- if .context.Values.backend.securityContext.enabled }}
  securityContext:
    {{- omit .context.Values.backend.securityContext "enabled" | toYaml | nindent 4 }}
  {{- end }}
  env:
    {{- include "secobserve.backendEnv" .context | nindent 4 }}
  command:
    - sh
    - -c
    - |
      echo 'Waiting for database migrations to be applied...'

      until python manage.py migrate --check >/dev/null 2>&1; do
          printf "."
          sleep 5;
      done;

      echo 'Migrations OK ✓'
  resources:
    {{- include "secobserve.backendResources" . | nindent 4 }}
{{- end -}}

{{/* Pod level scheduling and security settings shared by all workloads. */}}
{{- define "secobserve.podPlacement" -}}
{{- with .Values.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with .Values.hostAliases }}
hostAliases:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with .Values.topologySpreadConstraints }}
topologySpreadConstraints:
  {{- tpl (toYaml .) $ | nindent 2 }}
{{- end }}
{{- with .Values.nodeSelector }}
nodeSelector:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with .Values.affinity }}
affinity:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with .Values.tolerations }}
tolerations:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- if .Values.securityContext.enabled }}
securityContext:
  {{- omit .Values.securityContext "enabled" | toYaml | nindent 2 }}
{{- end }}
{{- end -}}

