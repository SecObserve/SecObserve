{% autoescape off %}
Hello{{ first_name }},

{{ first_line }}

{{ message }}

Product:     {{ observation_log.observation.product.name }}
Observation: {{ observation_log.observation.title }}
{% if observation_log.severity %}Severity:    {{ observation_log.severity }}
{% endif %}{% if observation_log.status %}Status:      {{ observation_log.status }}
{% endif %}{% if observation_log.priority %}Priority:    {{ observation_log.priority }}
{% endif %}{% if observation_log.comment %}Comment:     {{ observation_log.comment }}
{% endif %}URL:         {{ assessment_url }}

Regards,

SecObserve
{% endautoescape %}
