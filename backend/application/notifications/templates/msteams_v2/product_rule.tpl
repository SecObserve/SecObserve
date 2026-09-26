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
                                "value": "{{ rule.product.name|escapejs }}"
                            },
                            {
                                "title": "Rule:",
                                "value": "{{ rule.name|escapejs }}"
                            },
                            {
                                "title": "Type:",
                                "value": "{{ rule.type|escapejs }}"
                            },
                            {
                                "title": "New severity:",
                                "value": "{{ rule.new_severity|escapejs }}"
                            },
                            {
                                "title": "New status:",
                                "value": "{{ rule.new_status|escapejs }}"
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View product rule {{ rule.name|escapejs }}",
                        "url": "{{ rule_url|escapejs }}"
                    }
                ]
            }
        }
    ]
}
