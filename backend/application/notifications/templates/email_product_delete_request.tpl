{% autoescape off %}
Hello{{ first_name }},

{{ requester_name }} requested deletion of {{ product_type }} {{ product.name }}.

Review {{ product_type }} {{ product.name }}: {{ product_url }}

Regards,

SecObserve
{% endautoescape %}
