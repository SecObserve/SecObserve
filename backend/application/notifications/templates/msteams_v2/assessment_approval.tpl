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
                            }{% if observation.branch %},
                            {
                                "title": "Branch:",
                                "value": "{{ observation.branch.name|escapejs }}"
                            }{% endif %}{% if observation.origin_service %},
                            {
                                "title": "Service:",
                                "value": "{{ observation.origin_service.name|escapejs }}"
                            }{% endif %},
                            {
                                "title": "Title:",
                                "value": "{{ observation.title|escapejs }}"
                            }{% if observation_log.severity %},
                            {
                                "title": "Severity:",
                                "value": "{{ observation_log.severity|escapejs }}"
                            }{% endif %}{% if observation_log.status %},
                            {
                                "title": "Status:",
                                "value": "{{ observation_log.status|escapejs }}"
                            }{% endif %}{% if observation_log.priority_changed %},
                            {
                                "title": "Priority:",
                                "value": "{{ observation_log.priority|escapejs }}"
                            }{% endif %}{% if observation_log.vex_justification %},
                            {
                                "title": "Justification:",
                                "value": "{{ observation_log.vex_justification|escapejs }}"
                            }{% endif %}{% if observation_log.comment %},
                            {
                                "title": "Comment:",
                                "value": "{{ observation_log.comment|escapejs }}"
                            }{% endif %}
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
