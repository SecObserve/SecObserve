{
	"type": "mrkdwn",
	"text": "*{{ first_line }}*\n\nProduct: {{ observation.product.name }}\n\nSeverity: {{ observation.current_severity }}\n\nStatus: {{ observation.current_status }}\n\n{% if observation.current_priority %}Priority: {{ observation.current_priority }}{% endif %}\n\nURL: {{ observation_url }}"
}
