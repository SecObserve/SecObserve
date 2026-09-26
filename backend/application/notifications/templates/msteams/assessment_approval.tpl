{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "{{ first_line|escapejs }}",
    "summary": "{{ first_line|escapejs }}",
    "sections": [{
        "facts": [{
            "name": "Product:",
            "value": "{{ observation.product.name|escapejs }}"
        }{% if observation.branch %}, {
            "name": "Branch:",
            "value": "{{ observation.branch.name|escapejs }}"
        }{% endif %}{% if observation.origin_service %}, {
            "name": "Service:",
            "value": "{{ observation.origin_service.name|escapejs }}"
        }{% endif %}, {
            "name": "Title:",
            "value": "{{ observation.title|escapejs }}"
        }{% if observation_log.severity %}, {
            "name": "Severity:",
            "value": "{{ observation_log.severity|escapejs }}"
        }{% endif %}{% if observation_log.status %}, {
            "name": "Status:",
            "value": "{{ observation_log.status|escapejs }}"
        }{% endif %}{% if observation_log.priority_changed %}, {
            "name": "Priority:",
            "value": "{{ observation_log.priority|escapejs }}"
        }{% endif %}{% if observation_log.vex_justification %}, {
            "name": "Justification:",
            "value": "{{ observation_log.vex_justification|escapejs }}"
        }{% endif %}{% if observation_log.comment %}, {
            "name": "Comment:",
            "value": "{{ observation_log.comment|escapejs }}"
        }{% endif %}],
        "markdown": true
    }],
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View assessment for observation {{ observation.title|escapejs }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ observation_log_url|escapejs }}"
                }
            ]
        }
    ]
}
