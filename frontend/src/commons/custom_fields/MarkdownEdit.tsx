import {
    BlockTypeSelect,
    BoldItalicUnderlineToggles,
    CodeToggle,
    CreateLink,
    DiffSourceToggleWrapper,
    InsertImage,
    InsertTable,
    InsertThematicBreak,
    ListsToggle,
    MDXEditor,
    Separator,
    diffSourcePlugin,
    headingsPlugin,
    imagePlugin,
    linkDialogPlugin,
    linkPlugin,
    listsPlugin,
    markdownShortcutPlugin,
    maxLengthPlugin,
    quotePlugin,
    tablePlugin,
    thematicBreakPlugin,
    toolbarPlugin,
} from "@mdxeditor/editor";
import "@mdxeditor/editor/style.css";
// @ts-expect-error Types are expected but none could be found
import { basicDark } from "cm6-theme-basic-dark";
// @ts-expect-error Types are expected but none could be found
import { basicLight } from "cm6-theme-basic-light";
import { Labeled } from "react-admin";

import { getTheme } from "../user_settings/functions";
import "./MarkdownEdit.css";

interface MarkdownEditProps {
    label: string;
    initialValue: string;
    setValue: (value: string) => void;
    overlayContainer?: HTMLDivElement | null;
    maxLength?: number;
    autoFocus?: boolean;
}

const MarkdownEdit = ({ label, initialValue, setValue, overlayContainer, maxLength, autoFocus }: MarkdownEditProps) => {
    const mdxeditor_theme = getTheme() == "dark" ? "dark-theme" : "light-theme";
    const codemirror_theme = getTheme() == "dark" ? basicDark : basicLight;

    if (!maxLength) {
        maxLength = Infinity;
    }

    const allPlugins = () => [
        toolbarPlugin({
            toolbarContents: () => (
                <DiffSourceToggleWrapper>
                    <BoldItalicUnderlineToggles />
                    <CodeToggle />
                    <Separator />
                    <ListsToggle />
                    <Separator />
                    <BlockTypeSelect />
                    <Separator />
                    <CreateLink />
                    <InsertImage />
                    <Separator />
                    <InsertTable />
                    <InsertThematicBreak />
                    <Separator />
                </DiffSourceToggleWrapper>
            ),
        }),
        listsPlugin(),
        quotePlugin(),
        headingsPlugin(),
        imagePlugin(),
        linkPlugin(),
        linkDialogPlugin(),
        tablePlugin(),
        thematicBreakPlugin(),
        markdownShortcutPlugin(),
        diffSourcePlugin({
            diffMarkdown: initialValue,
            viewMode: "rich-text",
            codeMirrorExtensions: [codemirror_theme],
        }),
        maxLengthPlugin(maxLength),
    ];

    return (
        <Labeled label={label} sx={{ marginBottom: 2 }}>
            <MDXEditor
                overlayContainer={overlayContainer}
                // className="dark-theme dark-editor"
                contentEditableClassName="prose"
                className={mdxeditor_theme}
                markdown={initialValue}
                onChange={(markdown) => setValue(markdown ?? "")}
                plugins={allPlugins()}
                autoFocus={autoFocus}
            />
        </Labeled>
    );
};

export default MarkdownEdit;
