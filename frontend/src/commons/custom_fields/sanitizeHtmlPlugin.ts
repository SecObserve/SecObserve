import {
    GenericHTMLNode,
    type KnownHTMLTagType,
    type MdastHTMLNode,
    type MdastImportVisitor,
    type MdxNodeType,
    type SerializedGenericHTMLNode,
    addImportVisitor$,
    addLexicalNode$,
    isMdastHTMLNode,
    lexical,
    realmPlugin,
} from "@mdxeditor/editor";

type MdxJsxAttribute = ReturnType<GenericHTMLNode["getAttributes"]>[number];
type MdastHTMLAttributes = MdastHTMLNode["attributes"];

// Markdown content is untrusted, so raw HTML in the editor may only produce these tags.
// All other tags are shown as text. img is not listed, it is handled by the image plugin.
const ALLOWED_TAGS: ReadonlySet<string> = new Set([
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "caption",
    "cite",
    "code",
    "dd",
    "del",
    "details",
    "div",
    "dl",
    "dt",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "ins",
    "kbd",
    "li",
    "mark",
    "ol",
    "p",
    "pre",
    "q",
    "s",
    "samp",
    "small",
    "span",
    "strong",
    "sub",
    "summary",
    "sup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
    "var",
    "wbr",
]);

const VOID_TAGS: ReadonlySet<string> = new Set([
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]);

const GLOBAL_ATTRIBUTES: readonly string[] = ["title", "lang", "dir"];

const TAG_ATTRIBUTES: ReadonlyMap<string, readonly string[]> = new Map([
    ["a", ["href"]],
    ["blockquote", ["cite"]],
    ["del", ["cite"]],
    ["details", ["open"]],
    ["ins", ["cite"]],
    ["li", ["value"]],
    ["ol", ["start", "type"]],
    ["q", ["cite"]],
    ["td", ["align", "colspan", "rowspan"]],
    ["th", ["align", "colspan", "rowspan"]],
]);

const URL_ATTRIBUTES: ReadonlySet<string> = new Set(["href", "cite"]);

function isSafeUrl(value: string): boolean {
    try {
        const protocol = new URL(value).protocol;
        return protocol === "http:" || protocol === "https:";
    } catch {
        return false;
    }
}

function filterAttributes(tag: string, attributes: MdastHTMLAttributes): MdxJsxAttribute[] {
    const allowed = [...GLOBAL_ATTRIBUTES, ...(TAG_ATTRIBUTES.get(tag) ?? [])];
    return attributes.filter((attribute): attribute is MdxJsxAttribute => {
        // Spread attributes ({...x}) and expression values ({x}) are dropped
        if (attribute.type !== "mdxJsxAttribute") {
            return false;
        }
        const value = attribute.value;
        if (value !== null && value !== undefined && typeof value !== "string") {
            return false;
        }
        // Only allowlisted attributes, so event handlers, style, id, name, etc. are dropped
        if (!allowed.includes(attribute.name)) {
            return false;
        }
        if (URL_ATTRIBUTES.has(attribute.name)) {
            return typeof value === "string" && isSafeUrl(value);
        }
        return true;
    });
}

// Text representation of the opening tag, e.g. <iframe src="https://example.com">
function formatOpeningTag(tag: string, attributes: MdastHTMLAttributes): string {
    const parts = attributes.map((attribute) => {
        if (attribute.type !== "mdxJsxAttribute") {
            return `{${attribute.value}}`;
        }
        const value = attribute.value;
        if (value === null || value === undefined) {
            return attribute.name;
        }
        if (typeof value === "string") {
            return `${attribute.name}="${value}"`;
        }
        return `${attribute.name}={${value.value}}`;
    });
    const content = [tag, ...parts].join(" ");
    return VOID_TAGS.has(tag) ? `<${content} />` : `<${content}>`;
}

// Keeps tag and attributes of the HTML element unchanged, so the exported Markdown is the same as the imported one
// (GenericHTMLNode's export visitor also handles subclasses). Only the DOM inside the editor is rendered safely:
// Allowed tags with filtered attributes only, all other tags as a container that shows the tags as text.
class SafeHTMLNode extends GenericHTMLNode {
    static getType(): string {
        return "secobserve-safe-html";
    }

    static clone(node: SafeHTMLNode): SafeHTMLNode {
        return new SafeHTMLNode(node.getTag(), node.getNodeType(), node.getAttributes(), node.getKey());
    }

    static importJSON(serializedNode: SerializedGenericHTMLNode): SafeHTMLNode {
        const node = $createSafeHTMLNode(serializedNode.tag, serializedNode.mdxType, serializedNode.attributes);
        node.setFormat(serializedNode.format);
        node.setIndent(serializedNode.indent);
        node.setDirection(serializedNode.direction);
        return node;
    }

    // GenericHTMLNode.exportJSON hardcodes the type "generic-html", but Lexical requires it to match getType(),
    // otherwise copying a selection that contains this node fails.
    exportJSON(): SerializedGenericHTMLNode {
        return { ...super.exportJSON(), type: SafeHTMLNode.getType() } as unknown as SerializedGenericHTMLNode;
    }

    createDOM(): HTMLElement {
        const tag = this.getTag();
        const attributes = this.getAttributes();

        if (ALLOWED_TAGS.has(tag)) {
            const element = document.createElement(tag);
            filterAttributes(tag, attributes).forEach((attribute) => {
                // filterAttributes only returns string values or attributes without value
                element.setAttribute(attribute.name, typeof attribute.value === "string" ? attribute.value : "");
            });
            return element;
        }

        // The tags are shown with CSS pseudo-elements (see MarkdownEdit.css), so their text
        // is never parsed as HTML and the content between them remains editable
        const element = document.createElement(this.isInline() ? "span" : "div");
        element.className = "raw-html-tag";
        element.dataset.openTag = formatOpeningTag(tag, attributes);
        if (!VOID_TAGS.has(tag)) {
            element.dataset.closeTag = `</${tag}>`;
        }
        return element;
    }
}

function $createSafeHTMLNode(tag: KnownHTMLTagType, type: MdxNodeType, attributes: MdxJsxAttribute[]): SafeHTMLNode {
    return lexical.$applyNodeReplacement(new SafeHTMLNode(tag, type, attributes));
}

// GenericHTMLNode puts all attributes unfiltered into the DOM. GenericHTMLNodes are not only created when importing
// Markdown, but also from Lexical JSON, e.g. when pasting content with the type application/x-lexical-editor,
// which can be crafted by any web page. The replacement turns every GenericHTMLNode into a SafeHTMLNode,
// because $createGenericHTMLNode and GenericHTMLNode.importJSON both call $applyNodeReplacement.
// It must be registered after GenericHTMLNode (by the core plugin), because the last registration of a type wins.
const genericHTMLNodeReplacement: lexical.LexicalNodeReplacement = {
    replace: GenericHTMLNode,
    with: (node: GenericHTMLNode) => new SafeHTMLNode(node.getTag(), node.getNodeType(), node.getAttributes()),
    withKlass: SafeHTMLNode,
};

// MDXEditor's MdastHTMLVisitor (priority -100) converts a <span> with only a style attribute into styled text,
// which would allow arbitrary CSS in the editor. This visitor handles the same nodes before it, so all HTML
// elements become SafeHTMLNodes.
const SafeHTMLVisitor: MdastImportVisitor<MdastHTMLNode> = {
    testNode: isMdastHTMLNode,
    visitNode({ mdastNode, actions }) {
        // All attributes are kept, including expression attributes, to export them unchanged.
        // GenericHTMLNode is typed with MdxJsxAttribute only, but MDXEditor passes all attributes as well.
        const attributes = mdastNode.attributes as MdxJsxAttribute[];
        actions.addAndStepInto($createSafeHTMLNode(mdastNode.name, mdastNode.type, attributes));
    },
    priority: -50,
};

export const sanitizeHtmlPlugin = realmPlugin({
    init(realm) {
        realm.pubIn({
            // addLexicalNode$ is typed for node classes only, but the nodes are passed to Lexical,
            // which accepts node replacements as well
            [addLexicalNode$]: [SafeHTMLNode, genericHTMLNodeReplacement as unknown as typeof SafeHTMLNode],
            [addImportVisitor$]: SafeHTMLVisitor,
        });
    },
});
