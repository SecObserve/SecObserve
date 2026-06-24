{# MS Teams Workflows (Power Automate) payload — Adaptive Card. MessageCard sibling: msteams_task_exception.tpl #}
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
                        "text": "Exception {{ exception_class|escapejs }} has occured while processing background task",
                        "weight": "Bolder",
                        "size": "Medium",
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
