{% autoescape off %}{
	"type": "mrkdwn",
	"text": "{% filter escapejs %}*{{ first_line }}*

Product: {{ observation.product.name }}

{% if observation.branch %}Branch: {{ observation.branch.name }}

{% endif %}{% if observation.origin_service %}Service: {{ observation.origin_service.name }}

{% endif %}Title: {{ observation.title }}

{% if observation.vulnerability_id %}Vulnerability ID: {{ observation.vulnerability_id }}

{% endif %}{% if observation.origin_component_name_version %}Component: {{ observation.origin_component_name_version }}

{% endif %}Severity: {{ observation.current_severity }}

{% if observation.cvss4_score %}CVSS 4 score: {{ observation.cvss4_score }}

{% endif %}{% if observation.cvss3_score %}CVSS 3 score: {{ observation.cvss3_score }}

{% endif %}{% if observation.epss_score %}EPSS score (%): {{ observation.epss_score }}

{% endif %}Status: {{ observation.current_status }}

{% if observation.current_priority %}Priority: {{ observation.current_priority }}

{% endif %}{% if observation.scanner %}Scanner: {{ observation.scanner }}

{% endif %}URL: {{ observation_url }}{% endfilter %}"
}{% endautoescape %}
