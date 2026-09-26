{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "{{ first_line|escapejs }}",
    "summary": "{{ first_line|escapejs }}",
    "sections": [{
        "facts": [{
            "name": "Product:",
            "value": "{{ rule.product.name|escapejs }}"
        }, {
            "name": "Rule:",
            "value": "{{ rule.name|escapejs }}"
        }, {
            "name": "Type:",
            "value": "{{ rule.type|escapejs }}"
        }, {
            "name": "New severity:",
            "value": "{{ rule.new_severity|escapejs }}"
        }, {
            "name": "New status:",
            "value": "{{ rule.new_status|escapejs }}"
        }],
        "markdown": true
    }],
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View product rule {{ rule.name|escapejs }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ rule_url|escapejs }}"
                }
            ]
        }
    ]
}
