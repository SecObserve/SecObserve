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
                        "text": "Exception {{ exception_class|escapejs }} has occured while processing background task",
                        "weight": "bolder",
                        "size": "medium",
                        "wrap": true
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Function:",
                                "value": "{{ function|escapejs }}"
                            },
                            {
                                "title": "Arguments:",
                                "value": "{{ arguments|escapejs }}"
                            },
                            {
                                "title": "User:",
                                "value": "{{ user.full_name|escapejs }}"
                            },
                            {
                                "title": "Exception class:",
                                "value": "{{ exception_class|escapejs }}"
                            },
                            {
                                "title": "Exception message:",
                                "value": "{{ exception_message|escapejs }}"
                            },
                            {
                                "title": "Timestamp:",
                                "value": "{{ date_time|date:"Y-m-d H:i:s.u"|escapejs }}"
                            },
                            {
                                "title": "Trace:",
                                "value": "{{ exception_trace|escapejs }}"
                            }
                        ]
                    }
                ]
            }
        }
    ]
}
