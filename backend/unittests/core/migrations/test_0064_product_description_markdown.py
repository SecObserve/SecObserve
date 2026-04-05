from html_to_markdown import convert

from unittests.base_test_case import BaseTestCase


class TestMarkdownConversion(BaseTestCase):
    def test_convert_markdown(self):
        html_description = """<h1>Heading 1</h1><h2>Heading 2</h2><ul><li><p><strong>bold</strong></p></li><li><p><em>italics</em></p></li><li><p><u>underscore</u></p></li><li><p><s><u>strikethrough</u></s></p></li></ul><ol><li><p>line 1</p></li><li><p>line 2</p></li></ol><p><code>code</code></p><p><a target="_blank" rel="noopener noreferrer nofollow" href="https://secobserve.github.io/SecObserve/">SecObserve</a></p>"""
        markdown_description = convert(html_description)
        self.assertEqual(
            """# Heading 1

## Heading 2

- **bold**

- *italics*

- underscore

- ~~strikethrough~~

1. line 1

2. line 2

`code`

[SecObserve](https://secobserve.github.io/SecObserve/)
""",
            markdown_description.get("content"),
        )
