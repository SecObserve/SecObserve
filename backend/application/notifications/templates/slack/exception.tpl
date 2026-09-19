{
	"type": "mrkdwn",
	"text": "*Exception {{ exception_class|escapejs }} has occured*\n\n*Exception class:*\n{{ exception_class|escapejs }}\n\n*Exception message:*\n{{ exception_message|escapejs }}\n\n*Timestamp:*\n{{ date_time|date:"Y-m-d H:i:s.u"|escapejs }}\n\n*Trace:*\n{{ exception_trace|escapejs }}"
}
