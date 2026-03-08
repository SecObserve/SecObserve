{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "Exception {{ exception_class }} has occured",
    "summary": "Exception {{ exception_class }} has occured",
    "sections": [{
        "facts": [{
            "name": "Exception class:",
            "value": "{{ exception_class }}"
        }, {
            "name": "Exception message:",
            "value": "{{ exception_message }}"
        }, {
            "name": "Timestamp:",
            "value": "{{ date_time|date:"Y-m-d H:i:s.u" }}"
        }, {
            "name": "Trace:",
            "value": "{{ exception_trace }}"
        }],
        "markdown": true
    }],
}
