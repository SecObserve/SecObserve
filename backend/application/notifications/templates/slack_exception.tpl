{
	"type": "mrkdwn",
	"text": "*Exception {{ exception_class }} has occured*\n\n*Exception class:*\n{{ exception_class }}\n\n*Exception message:*\n{{ exception_message }}\n\n*Timestamp:*\n{{ date_time|date:"Y-m-d H:i:s.u" }}\n\n*Trace:*\n{{ exception_trace }}"
}
