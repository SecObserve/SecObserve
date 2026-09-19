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
                                "title": "Title:",
                                "value": "{{ observation.title|escapejs }}"
                            },
                            {
                                "title": "Severity:",
                                "value": "{{ observation_log.severity|escapejs }}"
                            },
                            {
                                "title": "Status:",
                                "value": "{{ observation_log.status|escapejs }}"
                            },
                            {
                                "title": "Comment:",
                                "value": "{{ observation_log.comment|escapejs }}"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View assessment for observation {{ observation.title|escapejs }}",
                        "url": "{{ observation_log_url|escapejs }}"
                    }
                ]
            }
        }
    ]
}
