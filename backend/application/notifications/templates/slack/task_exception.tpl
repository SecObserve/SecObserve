{% autoescape off %}{
	"type": "mrkdwn",
	"text": "{% filter escapejs %}*Exception {{ exception_class }} has occured while processing background task*

*Function:*
{{ function }}

*Arguments:*
{{ arguments }}

*User:*
{{ user.full_name }}

*Exception class:*
{{ exception_class }}

*Exception message:*
{{ exception_message }}

*Timestamp:*
{{ date_time|date:"Y-m-d H:i:s.u" }}

*Trace:*
{{ exception_trace }}{% endfilter %}"
}{% endautoescape %}
