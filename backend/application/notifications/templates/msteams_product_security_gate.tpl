{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "Security gate for product {{ product.name|escapejs }} has changed to {{ security_gate_status|escapejs }}",
    "summary": "Security gate for product {{ product.name|escapejs }} has changed to {{ security_gate_status|escapejs }}",
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View Product {{ product.name|escapejs }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ product_url|escapejs }}"
                }
            ]
        }
    ]
}
