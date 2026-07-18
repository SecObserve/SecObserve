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
                        "text": "{{ first_line }}",
                        "weight": "bolder",
                        "size": "medium",
                        "wrap": true
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Severity:",
                                "value": "{{ observation.current_severity }}"
                            },
                            {
                                "title": "Status:",
                                "value": "{{ observation.current_status }}"
                            },
                            {
                                "title": "Priority:",
                                "value": "{{ observation.current_priority }}"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View observation title {{ observation.title }}",
                        "url": "{{ url }}"
                    }
                ]
            }
        }
    ]
}
