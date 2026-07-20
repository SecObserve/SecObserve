{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "{{ first_line|escapejs }}",
    "summary": "{{ first_line|escapejs }}",
    "sections": [{
        "text": "{{ message|escapejs }}",
        "facts": [{
            "name": "Product:",
            "value": "{{ observation_log.observation.product.name|escapejs }}"
        }, {
            "name": "Observation:",
            "value": "{{ observation_log.observation.title|escapejs }}"
        }, {
            "name": "Severity:",
            "value": "{{ observation_log.severity|escapejs }}"
        }, {
            "name": "Status:",
            "value": "{{ observation_log.status|escapejs }}"
        }, {
            "name": "Priority:",
            "value": "{{ observation_log.priority|escapejs }}"
        }],
        "markdown": true
    }],
    "potentialAction": [{
        "@type": "OpenUri",
        "name": "Open assessment",
        "targets": [{
            "os": "default",
            "uri": "{{ assessment_url|escapejs }}"
        }]
    }]
}
