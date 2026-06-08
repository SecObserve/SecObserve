{
	"type": "mrkdwn",
	"text": "*{{ first_line|escapejs }}*\n\nProduct: {{ observation.product.name|escapejs }}\n\nSeverity: {{ observation.current_severity|escapejs }}\n\nStatus: {{ observation.current_status|escapejs }}\n\n{% if observation.current_priority %}Priority: {{ observation.current_priority|escapejs }}{% endif %}\n\nURL: {{ observation_url|escapejs }}"
}
