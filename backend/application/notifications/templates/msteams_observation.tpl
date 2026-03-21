{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "{{ first_line }}",
    "summary": "{{ first_line }}",
    "sections": [{
        "facts": [{
            "name": "Product:",
            "value": "{{ observation.product.name }}"
        }, {
            "name": "Severity:",
            "value": "{{ observation.current_severity }}"
        }, {
            "name": "Status:",
            "value": "{{ observation.current_status }}"
        }, {
            "name": "Priority:",
            "value": "{{ observation.current_priority }}"
        }],
        "markdown": true
    }],
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View observation {{ observation.title }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ observation_url }}"
                }
            ]
        }
    ]
}
