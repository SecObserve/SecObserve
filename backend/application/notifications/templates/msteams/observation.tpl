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
        }{% if observation.vulnerability_id %}, {
            "name": "Vulnerability ID:",
            "value": "{{ observation.vulnerability_id|escapejs }}"
        }{% endif %}{% if observation.origin_component_name_version %}, {
            "name": "Component:",
            "value": "{{ observation.origin_component_name_version|escapejs }}"
        }{% endif %}, {
            "name": "Severity:",
            "value": "{{ observation.current_severity|escapejs }}"
        }{% if observation.cvss4_score %}, {
            "name": "CVSS 4 score:",
            "value": "{{ observation.cvss4_score|escapejs }}"
        }{% endif %}{% if observation.cvss3_score %}, {
            "name": "CVSS 3 score:",
            "value": "{{ observation.cvss3_score|escapejs }}"
        }{% endif %}{% if observation.epss_score %}, {
            "name": "EPSS score (%):",
            "value": "{{ observation.epss_score|escapejs }}"
        }{% endif %}, {
            "name": "Status:",
            "value": "{{ observation.current_status|escapejs }}"
        }{% if observation.current_priority %}, {
            "name": "Priority:",
            "value": "{{ observation.current_priority|escapejs }}"
        }{% endif %}{% if observation.scanner %}, {
            "name": "Scanner:",
            "value": "{{ observation.scanner|escapejs }}"
        }{% endif %}],
        "markdown": true
    }],
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View observation {{ observation.title|escapejs }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ observation_url|escapejs }}"
                }
            ]
        }
    ]
}
