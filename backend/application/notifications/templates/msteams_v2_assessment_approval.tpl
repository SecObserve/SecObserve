{
    "type": "message",
    "attachments": [{
        "contentType": "application/vnd.microsoft.card.adaptive",
        "contentUrl": null,
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [{
                "type": "TextBlock",
                "text": "{{ first_line|escapejs }}",
                "weight": "bolder",
                "size": "medium",
                "wrap": true
            }, {
                "type": "TextBlock",
                "text": "{{ message|escapejs }}",
                "wrap": true
            }, {
                "type": "FactSet",
                "facts": [{
                    "title": "Product:",
                    "value": "{{ observation_log.observation.product.name|escapejs }}"
                }, {
                    "title": "Observation:",
                    "value": "{{ observation_log.observation.title|escapejs }}"
                }, {
                    "title": "Severity:",
                    "value": "{{ observation_log.severity|escapejs }}"
                }, {
                    "title": "Status:",
                    "value": "{{ observation_log.status|escapejs }}"
                }, {
                    "title": "Priority:",
                    "value": "{{ observation_log.priority|escapejs }}"
                }]
            }],
            "actions": [{
                "type": "Action.OpenUrl",
                "title": "Open assessment",
                "url": "{{ assessment_url|escapejs }}"
            }]
        }
    }]
}
