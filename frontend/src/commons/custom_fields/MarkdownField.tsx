import Markdown from "markdown-to-jsx";
import { marked } from "marked";
import { Fragment } from "react";

import { useLinkStyles } from "../../commons/layout/themes";
import { getSettingTheme } from "../user_settings/functions";
import LabeledTextField from "./LabeledTextField";

interface MarkdownProps {
    content: string;
    label: string;
}

// copied from https://stackoverflow.com/a/77300386
function isMarkdownValue(value: string): boolean {
    const tokenTypes: string[] = [];

    marked(value, {
        walkTokens: (token) => {
            tokenTypes.push(token.type);
        },
    });

    const isMarkdown = [
        "space",
        "code",
        "fences",
        "heading",
        "hr",
        "link",
        "blockquote",
        "list",
        "html",
        "def",
        "table",
        "lheading",
        "escape",
        "tag",
        "reflink",
        "strong",
        "codespan",
        "url",
    ].some((tokenType) => tokenTypes.includes(tokenType));

    return isMarkdown;
}

const MarkdownField = (props: MarkdownProps) => {
    const { classes } = useLinkStyles({ setting_theme: getSettingTheme() });

    return (
        <Fragment>
            {isMarkdownValue(props.content) && (
                <Markdown
                    style={{
                        fontSize: "0.875rem",
                        fontFamily: "Roboto",
                        lineHeight: 1.43,
                    }}
                    options={{
                        overrides: {
                            a: {
                                props: {
                                    className: classes.link,
                                },
                            },
                        },
                    }}
                >
                    {props.content}
                </Markdown>
            )}
            {!isMarkdownValue(props.content) && <LabeledTextField label={props.label} text={props.content} />}
        </Fragment>
    );
};

export default MarkdownField;
