import { FormControl } from "@mui/material";
import { BooleanInput, BooleanInputProps } from "react-admin";

// A FormControl gets the same dense margins from the theme as the other filter inputs,
// the medium switch has about the height of their text fields
export const DefaultBranchInput = (props: BooleanInputProps) => (
    <FormControl fullWidth={false}>
        <BooleanInput {...props} size="medium" />
    </FormControl>
);
