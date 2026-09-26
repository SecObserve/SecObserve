{
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": null,
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "{{ first_line|escapejs }}",
                        "weight": "bolder",
                        "size": "medium",
                        "wrap": true
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Title:",
                                "value": "{{ observation.title|escapejs }}"
                            },
                            {
                                "title": "Severity:",
                                "value": "{{ observation.current_severity|escapejs }}"
                            },
                            {
                                "title": "Status:",
                                "value": "{{ observation.current_status|escapejs }}"
                            }{% if observation.current_priority %},
                            {
                                "title": "Priority:",
                                "value": "{{ observation.current_priority|escapejs }}"
                            }{% endif %}
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View observation title {{ observation.title|escapejs }}",
                        "url": "{{ url|escapejs }}"
                    }
                ]
            }
        }
    ]
}
