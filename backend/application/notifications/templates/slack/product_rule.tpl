{
	"type": "mrkdwn",
	"text": "*{{ first_line|escapejs }}*\n\nProduct: {{ rule.product.name|escapejs }}\n\nRule: {{ rule.name|escapejs }}\n\nType: {{ rule.type|escapejs }}\n\n{% if rule.new_severity %}New severity: {{ rule.new_severity|escapejs }}{% endif %}\n\n{% if rule.new_status %}New status: {{ rule.new_status|escapejs }}{% endif %}\n\nURL: {{ rule_url|escapejs }}"
}
