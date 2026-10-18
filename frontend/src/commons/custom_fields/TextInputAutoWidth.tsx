import { TextInput, TextInputProps } from "react-admin";
import { useWatch } from "react-hook-form";

import { useAutoWidth } from "./autoWidth";

// Starts small and grows with the entered text.
export const TextInputAutoWidth = (props: TextInputProps) => {
    const value = useWatch({ name: props.source });
    // 30px: horizontal padding of the outlined input and room for the cursor
    const width = useAutoWidth(String(value ?? ""), 30);
    return <TextInput {...props} sx={{ width: width }} />;
};
