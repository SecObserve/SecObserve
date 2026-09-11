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
                                "title": "Product:",
                                "value": "{{ observation.product.name|escapejs }}"
                            },
                            {
                                "title": "Severity:",
                                "value": "{{ observation.current_severity|escapejs }}"
                            },
                            {
                                "title": "Status:",
                                "value": "{{ observation.current_status|escapejs }}"
                            },
                            {
                                "title": "Priority:",
                                "value": "{{ observation.current_priority|escapejs }}"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View observation {{ observation.title|escapejs }}",
                        "url": "{{ observation_url|escapejs }}"
                    }
                ]
            }
        }
    ]
}
