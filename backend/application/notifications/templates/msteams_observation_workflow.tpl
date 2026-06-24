{# MS Teams Workflows (Power Automate) payload — Adaptive Card. MessageCard sibling: msteams_observation.tpl #}
{
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "{{ first_line|escapejs }}",
                        "weight": "Bolder",
                        "size": "Medium",
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
