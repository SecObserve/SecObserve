{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "Exception {{ exception_class|escapejs }} has occured while processing background task",
    "summary": "Exception {{ exception_class|escapejs }} has occured",
    "sections": [{
        "facts": [{
            "name": "Function:",
            "value": "{{ function|escapejs }}"
        }, {
            "name": "Arguments:",
            "value": "{{ arguments|escapejs }}"
        }, {
            "name": "User:",
            "value": "{{ user.full_name|escapejs }}"
        }, {
            "name": "Exception class:",
            "value": "{{ exception_class|escapejs }}"
        }, {
            "name": "Exception message:",
            "value": "{{ exception_message|escapejs }}"
        }, {
            "name": "Timestamp:",
            "value": "{{ date_time|date:"Y-m-d H:i:s.u"|escapejs }}"
        }, {
            "name": "Trace:",
            "value": "{{ exception_trace|escapejs }}"
        }],
        "markdown": true
    }],
}
