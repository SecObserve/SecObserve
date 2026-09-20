{% autoescape off %}{
	"type": "mrkdwn",
	"text": "{% filter escapejs %}*{{ first_line }}*

Title: {{ observation.title }}

Severity: {{ observation.current_severity }}

Status: {{ observation.current_status }}

{% if observation.current_priority %}Priority: {{ observation.current_priority }}

{% endif %}URL: {{ url }}{% endfilter %}"
}{% endautoescape %}
