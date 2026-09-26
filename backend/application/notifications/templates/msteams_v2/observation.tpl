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
                            }{% if observation.vulnerability_id %},
                            {
                                "title": "Vulnerability ID:",
                                "value": "{{ observation.vulnerability_id|escapejs }}"
                            }{% endif %}{% if observation.origin_component_name_version %},
                            {
                                "title": "Component:",
                                "value": "{{ observation.origin_component_name_version|escapejs }}"
                            }{% endif %},
                            {
                                "title": "Severity:",
                                "value": "{{ observation.current_severity|escapejs }}"
                            }{% if observation.cvss4_score %},
                            {
                                "title": "CVSS 4 score:",
                                "value": "{{ observation.cvss4_score|escapejs }}"
                            }{% endif %}{% if observation.cvss3_score %},
                            {
                                "title": "CVSS 3 score:",
                                "value": "{{ observation.cvss3_score|escapejs }}"
                            }{% endif %}{% if observation.epss_score %},
                            {
                                "title": "EPSS score (%):",
                                "value": "{{ observation.epss_score|escapejs }}"
                            }{% endif %},
                            {
                                "title": "Status:",
                                "value": "{{ observation.current_status|escapejs }}"
                            }{% if observation.current_priority %},
                            {
                                "title": "Priority:",
                                "value": "{{ observation.current_priority|escapejs }}"
                            }{% endif %}{% if observation.scanner %},
                            {
                                "title": "Scanner:",
                                "value": "{{ observation.scanner|escapejs }}"
                            }{% endif %}
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
