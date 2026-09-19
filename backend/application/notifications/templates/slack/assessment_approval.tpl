{
	"type": "mrkdwn",
	"text": "*{{ first_line|escapejs }}*\n\nProduct: {{ observation.product.name|escapejs }}\n\nTitle: {{ observation.title|escapejs }}\n\nSeverity: {{ observation_log.severity|escapejs }}\n\nStatus: {{ observation_log.status|escapejs }}\n\n{% if observation_log.comment %}Comment: {{ observation_log.comment|escapejs }}{% endif %}\n\nURL: {{ observation_log_url|escapejs }}"
}
