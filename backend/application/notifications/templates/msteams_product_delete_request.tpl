{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "{{ requester_name|escapejs }} requested deletion of {{ product_type|escapejs }} {{ product.name|escapejs }}",
    "summary": "{{ requester_name|escapejs }} requested deletion of {{ product_type|escapejs }} {{ product.name|escapejs }}",
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "Review {{ product_type|escapejs }} {{ product.name|escapejs }}",
            "targets": [
                {
                    "os": "default",
                    "uri": "{{ product_url|escapejs }}"
                }
            ]
        }
    ]
}
