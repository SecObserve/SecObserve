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
                        "text": "Security gate for product {{ product.name|escapejs }} has changed to {{ security_gate_status|escapejs }}",
                        "weight": "bolder",
                        "size": "medium",
                        "wrap": true
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View Product {{ product.name|escapejs }}",
                        "url": "{{ product_url|escapejs }}"
                    }
                ]
            }
        }
    ]
}
