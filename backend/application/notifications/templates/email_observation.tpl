{% autoescape off %}
Hello{{ first_name }},

{{ first_line }}

Product:  {{ observation.product.name}}
Title:    {{ observation.title }}
Severity: {{ observation.current_severity }}
Status:   {{ observation.current_status }}
{% if observation.current_priority %}Priority: {{ observation.current_priority }}{% endif %}
URL:      {{ observation_url }}

Regards,

SecObserve
{% endautoescape %}
