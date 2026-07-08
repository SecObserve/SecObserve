{% autoescape off %}
Hello{{ first_name }},

{{ requester_name }} requested deletion of {{ product_type }} {{ product_display_name }}.

Review {{ product_type }} {{ product_display_name }}: {{ product_url }}

Regards,

SecObserve
{% endautoescape %}
