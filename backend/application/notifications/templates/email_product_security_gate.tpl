{% autoescape off %}
Hello{{ first_name }},

The security gate for product {{ product.name }} has changed to {{ security_gate_status }}.

View product {{ product.name }}: {{ product_url }}

Regards,

SecObserve
{% endautoescape %}
