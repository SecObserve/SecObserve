{
    "type": "mrkdwn",
    "text": "*{{ first_line|escapejs }}*\n\n{{ message|escapejs }}\n\nProduct: {{ observation_log.observation.product.name|escapejs }}\n\nObservation: {{ observation_log.observation.title|escapejs }}{% if observation_log.severity %}\n\nSeverity: {{ observation_log.severity|escapejs }}{% endif %}{% if observation_log.status %}\n\nStatus: {{ observation_log.status|escapejs }}{% endif %}{% if observation_log.priority %}\n\nPriority: {{ observation_log.priority|escapejs }}{% endif %}\n\nURL: {{ assessment_url|escapejs }}"
}
