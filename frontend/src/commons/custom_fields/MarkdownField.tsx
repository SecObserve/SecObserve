import Markdown from "markdown-to-jsx";
import { marked } from "marked";
import { Fragment, HTMLAttributes } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";

import { useLinkStyles } from "../../commons/layout/themes";
import { getPrismTheme } from "../functions";
import { getResolvedSettingTheme } from "../user_settings/functions";
import LabeledTextField from "./LabeledTextField";

declare global {
    interface Window {
        hljs?: {
            highlightElement: (el: HTMLElement) => void;
        };
    }
}
export {};

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

type CodeProps = HTMLAttributes<HTMLElement>;

function SyntaxHighlightedCode({ className, children, ...rest }: CodeProps) {
    // markdown-to-jsx tags fenced blocks with `lang-<language>`.
    // Inline code (`like this`) has no such class — render it as-is.
    const match = /lang-(\w+)/.exec(className ?? "");
    if (!match) {
        return (
            <code className={className} {...rest}>
                {children}
            </code>
        );
    }

    return (
        <SyntaxHighlighter
            language={match[1]}
            style={getPrismTheme()}
            PreTag="div" // markdown-to-jsx already wraps fenced blocks in <pre>; avoid nesting
        >
            {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
    );
}

const MarkdownField = (props: MarkdownProps) => {
    const { classes } = useLinkStyles({ setting_theme: getResolvedSettingTheme() });

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
                            code: SyntaxHighlightedCode,
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
