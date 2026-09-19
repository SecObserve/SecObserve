{% autoescape off %}
Hello{{ first_name }},

{{ first_line }}

Product:       {{ observation.product.name }}
{% if observation.branch %}Branch:        {{ observation.branch.name }}
{% endif %}{% if observation.origin_service %}Service:       {{ observation.origin_service.name }}
{% endif %}Title:         {{ observation.title }}
{% if observation_log.severity %}Severity:      {{ observation_log.severity }}
{% endif %}{% if observation_log.status %}Status:        {{ observation_log.status }}
{% endif %}{% if observation_log.priority_changed %}Priority:      {{ observation_log.priority }}
{% endif %}{% if observation_log.vex_justification %}Justification: {{ observation_log.vex_justification }}
{% endif %}{% if observation_log.comment %}Comment:       {{ observation_log.comment }}
{% endif %}URL:           {{ observation_log_url }}

Regards,

SecObserve
{% endautoescape %}
