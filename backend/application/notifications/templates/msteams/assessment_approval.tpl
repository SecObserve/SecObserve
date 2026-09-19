{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "{{ first_line|escapejs }}",
    "summary": "{{ first_line|escapejs }}",
    "sections": [{
        "facts": [{
            "name": "Product:",
            "value": "{{ observation.product.name|escapejs }}"
        }, {
            "name": "Title:",
            "value": "{{ observation.title|escapejs }}"
        }, {
            "name": "Severity:",
            "value": "{{ observation_log.severity|escapejs }}"
        }, {
            "name": "Status:",
            "value": "{{ observation_log.status|escapejs }}"
        }, {
            "name": "Comment:",
            "value": "{{ observation_log.comment|escapejs }}"
        }],
        "markdown": true
    }],
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View assessment for observation {{ observation.title|escapejs }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ observation_log_url|escapejs }}"
                }
            ]
        }
    ]
}
