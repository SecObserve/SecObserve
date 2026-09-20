{% autoescape off %}{
	"type": "mrkdwn",
	"text": "{% filter escapejs %}*Security gate for product {{ product.name }} has changed to {{ security_gate_status }}*

View Product <{{ product_url }}|{{ product.name }}>{% endfilter %}"
}{% endautoescape %}
