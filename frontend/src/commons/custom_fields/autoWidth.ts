import { useTheme } from "@mui/material";

let canvasContext: CanvasRenderingContext2D | null = null;

// Counting characters as 1ch each overestimates proportional fonts, so the text is measured instead.
const textWidth = (text: string, font: string): number => {
    canvasContext ??= document.createElement("canvas").getContext("2d");
    if (!canvasContext) {
        return text.length * 8;
    }
    canvasContext.font = font;
    return canvasContext.measureText(text).width;
};

// Width of an input that starts small and grows with its text, up to the width of AutocompleteInputWide.
// padding: the space of the input besides the text, e.g. for padding and buttons.
export const useAutoWidth = (text: string, padding: number): string => {
    const { body1 } = useTheme().typography;
    const width = textWidth(text, `${body1.fontWeight} ${body1.fontSize} ${body1.fontFamily}`);
    return `min(30em, max(10em, ${Math.ceil(width) + padding}px))`;
};
