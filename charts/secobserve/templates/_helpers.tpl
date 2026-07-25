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
