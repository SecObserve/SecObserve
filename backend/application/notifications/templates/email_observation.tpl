{% autoescape off %}
Hello{{ first_name }},

{{ first_line }}

Product:  {{ observation.product.name }}
{% if observation.branch %}Branch:   {{ observation.branch.name }}
{% endif %}{% if observation.origin_service %}Service:  {{ observation.origin_service.name }}
{% endif %}Title:    {{ observation.title }}
Severity: {{ observation.current_severity }}
Status:   {{ observation.current_status }}
{% if observation.current_priority %}Priority: {{ observation.current_priority }}
{% endif %}URL:      {{ observation_url }}

Regards,

SecObserve
{% endautoescape %}
