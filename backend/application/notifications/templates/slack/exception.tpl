{% autoescape off %}{
	"type": "mrkdwn",
	"text": "{% filter escapejs %}*Exception {{ exception_class }} has occured*

*Exception class:*
{{ exception_class }}

*Exception message:*
{{ exception_message }}

*Timestamp:*
{{ date_time|date:"Y-m-d H:i:s.u" }}

*Trace:*
{{ exception_trace }}{% endfilter %}"
}{% endautoescape %}
