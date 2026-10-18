import { AutocompleteInput, AutocompleteInputProps, RaRecord, useChoicesContext } from "react-admin";

import { useAutoWidth } from "./autoWidth";

const selectedText = (record: RaRecord | undefined, optionText: AutocompleteInputProps["optionText"]): string => {
    if (!record) {
        return "";
    }
    if (typeof optionText === "function") {
        return String(optionText(record) ?? "");
    }
    return String(record[typeof optionText === "string" ? optionText : "name"] ?? "");
};

// Starts small and grows with the text of the selected record.
// Must be the child of a ReferenceInput, whose ChoicesContext provides the selected record.
export const AutocompleteInputAutoWidth = (props: AutocompleteInputProps) => {
    const { selectedChoices } = useChoicesContext();
    // 86px: padding of the small outlined input (6 + 8 + 4), the clear and the popup button (65) and room for the cursor
    const width = useAutoWidth(selectedText(selectedChoices?.[0], props.optionText), 86);
    return <AutocompleteInput {...props} sx={{ width: width }} />;
};
