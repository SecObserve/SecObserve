{% autoescape off %}
Hello{{ first_name }},

{{ first_line }}

Product:       {{ rule.product.name }}
Rule:          {{ rule.name }}
Type:          {{ rule.type }}
{% if rule.new_severity %}New severity:  {{ rule.new_severity }}
{% endif %}{% if rule.new_status %}New status:    {{ rule.new_status }}
{% endif %}Requested by:  {{ rule.user.full_name }}
URL:           {{ rule_url }}

Regards,

SecObserve
{% endautoescape %}
