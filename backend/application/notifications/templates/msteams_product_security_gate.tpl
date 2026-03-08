{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "Security gate for product {{ product.name }} has changed to {{ security_gate_status }}",
    "summary": "Security gate for product {{ product.name }} has changed to {{ security_gate_status }}",
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View Product {{ product.name }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ product_url }}"
                }
            ]
        }
    ]
}
