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
                        "text": "Exception {{ exception_class }} has occured while processing background task",
                        "weight": "bolder",
                        "size": "medium",
                        "wrap": true
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Function:",
                                "value": "{{ function }}"
                            },
                            {
                                "title": "Arguments:",
                                "value": "{{ arguments }}"
                            },
                            {
                                "title": "User:",
                                "value": "{{ user.full_name }}"
                            },
                            {
                                "title": "Exception class:",
                                "value": "{{ exception_class }}"
                            },
                            {
                                "title": "Exception message:",
                                "value": "{{ exception_message }}"
                            },
                            {
                                "title": "Timestamp:",
                                "value": "{{ date_time|date:"Y-m-d H:i:s.u" }}"
                            },
                            {
                                "title": "Trace:",
                                "value": "{{ exception_trace }}"
                            }
                        ]
                    }
                ]
            }
        }
    ]
}
