{# MS Teams Workflows (Power Automate) payload — Adaptive Card. MessageCard sibling: msteams_product_security_gate.tpl #}
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
                        "type": "Container",
                        "bleed": true,
                        "style": "{% if security_gate_status == 'Failed' %}attention{% elif security_gate_status == 'Passed' %}good{% else %}default{% endif %}",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "{% if security_gate_status == 'Failed' %}🔴 Security gate failed{% elif security_gate_status == 'Passed' %}🟢 Security gate passed{% else %}⚪ Security gate disabled{% endif %}",
                                "weight": "Bolder",
                                "size": "Large",
                                "wrap": true
                            },
                            {
                                "type": "TextBlock",
                                "text": "{{ product.name|escapejs }}",
                                "spacing": "None",
                                "isSubtle": true,
                                "wrap": true
                            }
                        ]
                    },
                    {
                        "type": "FactSet",
                        "facts": [{% for stat in severity_stats %}{% if not forloop.first %},{% endif %}
                            {
                                "title": "{{ stat.label|escapejs }}",
                                "value": "{% if stat.count is not None %}{{ stat.count }}{% else %}n/a{% endif %}{% if stat.threshold is not None %} / allowed {{ stat.threshold }}{% endif %}"
                            }{% endfor %}
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View product {{ product.name|escapejs }}",
                        "url": "{{ product_url|escapejs }}"
                    }
                ]
            }
        }
    ]
}
