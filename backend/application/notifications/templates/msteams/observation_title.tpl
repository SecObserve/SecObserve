{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "{{ first_line|escapejs }}",
    "summary": "{{ first_line|escapejs }}",
    "sections": [{
        "facts": [{
            "name": "Severity:",
            "value": "{{ observation.current_severity|escapejs }}"
        }, {
            "name": "Status:",
            "value": "{{ observation.current_status|escapejs }}"
        }, {
            "name": "Priority:",
            "value": "{{ observation.current_priority|escapejs }}"
        }],
        "markdown": true
    }],
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View observation title {{ observation.title|escapejs }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ url|escapejs }}"
                }
            ]
        }
    ]
}
